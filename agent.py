"""
Smart Grading Assistant - Main Agent

A multi-agent system for automated academic grading with human oversight.
This capstone project demonstrates key concepts from the Google ADK course:

1. Multi-agent system (Sequential + Parallel)
2. Custom Tools (validate_rubric, grade_criterion, calculate_score)
3. Human-in-the-Loop (approval for edge cases)
4. Sessions & Memory (DatabaseSessionService)
5. Observability (LoggingPlugin)
6. Gemini model (bonus points)

Author: Rafael Ventura
Course: 5-Day AI Agents Intensive Course with Google
"""

import asyncio
import json
import logging
import os
import uuid

from dotenv import load_dotenv
from google.genai import types

from google.adk.agents import Agent, LlmAgent, SequentialAgent, ParallelAgent
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from typing import Any, List, Optional, Tuple

from utils.text_utils import slugify

try:
    from .tools.validate_rubric import validate_rubric
    from .tools.grade_criterion import grade_criterion
    from .tools.calculate_score import calculate_final_score
    from .tools.build_grades_payload import build_grades_payload
except ImportError:  # When running `python agent.py` directly inside capstone/
    from tools.validate_rubric import validate_rubric
    from tools.grade_criterion import grade_criterion
    from tools.calculate_score import calculate_final_score
    from tools.build_grades_payload import build_grades_payload

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "logs", "grading_agent.log")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_LITE = os.getenv("MODEL_LITE", "gemini-2.5-flash-lite")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Configure logging for observability
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
)

print("✅ Smart Grading Assistant - Loading...")

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_NAME = "capstone"
USER_ID = "teacher_01"

# Retry configuration for API calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Score thresholds for human approval
FAILING_THRESHOLD = 50  # Below this requires approval
EXCEPTIONAL_THRESHOLD = 90  # Above this requires approval

print("✅ Configuration loaded")

# =============================================================================
# RUBRIC GUARDRAIL PLUGIN
# Blocks grading agents if rubric has not been validated successfully.
# =============================================================================


class RubricGuardrailPlugin(BasePlugin):
    """Guardrail to ensure rubric is valid before running grading agents.

    This plugin runs before each agent. For agents that depend on a validated
    rubric, it checks the session state for a `validation_result` with status == "valid".
    
    Pattern: Uses before_agent_callback to return types.Content which skips
    the agent's execution gracefully without crashing the app.
    
    """

    def __init__(self) -> None:
        super().__init__(name="rubric_guardrail")
        self._blocked_agents: set = set()  # Track which agents were blocked

    def _normalize_validation_payload(self, payload: Any) -> Optional[dict]:
        """Normalize different payload formats into a dict or None."""
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            text = payload.lower()
            if any(keyword in text for keyword in ["invalid", "error", "missing", "failed"]):
                return {
                    "status": "invalid",
                    "errors": [
                        "Rubric validation failed - see validator response"
                    ],
                }
            if "valid" in text and "invalid" not in text:
                return {"status": "valid"}
        return None

    def _get_state_dict(self, callback_context: CallbackContext) -> dict:
        """Safely get state as dict from callback_context."""
        try:
            return callback_context.state.to_dict()
        except Exception:
            return {}

    def _get_rubric(self, callback_context: CallbackContext) -> Optional[dict]:
        """Get the latest rubric dict from state or invocation context."""
        state_dict = self._get_state_dict(callback_context)
        rubric = state_dict.get("rubric")
        if isinstance(rubric, dict):
            return rubric
        inv_ctx = getattr(callback_context, "_invocation_context", None)
        if inv_ctx:
            session_state = getattr(inv_ctx, "session_state", {}) or {}
            rubric = session_state.get("rubric")
            if isinstance(rubric, dict):
                return rubric
        return None

    def _get_validation_result(self, callback_context: CallbackContext) -> Optional[dict]:
        """Extract rubric validation status from session state.
        
        Primary source: state["rubric_validation"] (set by validate_rubric tool)
        Fallback: state["validation_result"] (LLM output text) parsed heuristically.
        """
        state_sources = []

        try:
            state_sources.append(callback_context.state.to_dict())
        except Exception:
            pass

        inv_ctx = getattr(callback_context, "_invocation_context", None)
        if inv_ctx:
            session_state = getattr(inv_ctx, "session_state", {}) or {}
            state_sources.append(session_state)

        for source in state_sources:
            if not source:
                continue
            for key in ("rubric_validation", "validation_result"):
                if key in source:
                    normalized = self._normalize_validation_payload(source.get(key))
                    if normalized:
                        return normalized

        return None

    def _is_rubric_valid(self, callback_context: CallbackContext) -> bool:
        """Check if rubric has been validated successfully."""
        validation_result = self._get_validation_result(callback_context)
        if validation_result is None:
            return False
        return validation_result.get("status") == "valid"

    def _ensure_dynamic_graders(self, agent: BaseAgent, callback_context: CallbackContext) -> None:
        rubric = self._get_rubric(callback_context)
        if not rubric:
            return
        dynamic_graders, grade_keys = build_graders_from_rubric(rubric)
        if not dynamic_graders:
            return
        agent.sub_agents = dynamic_graders
        try:
            callback_context.state["grader_output_keys"] = grade_keys
        except Exception:
            pass

    def _build_block_message(self, agent_name: str, callback_context: CallbackContext) -> str:
        """Build a user-friendly blocking message."""
        validation_result = self._get_validation_result(callback_context)
        errors = []
        if validation_result:
            errors = validation_result.get("errors", [])
        
        error_details = "\n".join(f"  - {e}" for e in errors) if errors else "  - Rubric was not validated"
        
        return f"""
🚫 **GRADING BLOCKED BY GUARDRAIL**

Agent '{agent_name}' cannot proceed because the rubric validation failed.

**Validation Errors:**
{error_details}

**What to do:**
1. Review the rubric structure
2. Ensure all required fields are present (name, criteria with name/max_score/description)
3. Submit a corrected rubric

No grading was performed. The pipeline has been safely stopped.
"""

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Block grading agents when rubric is not valid.
        
        Returns types.Content to skip the agent's execution gracefully.
        Returns None to allow normal execution.
        """
        # Define which agents require a valid rubric
        protected_agents = {
            "ParallelGraders",
            "AggregatorAgent",
            "ApprovalAgent",
            "FeedbackGeneratorAgent",
            # Also protect individual graders
            "Grader_Code_Quality",
            "Grader_Functionality",
            "Grader_Documentation",
        }

        if agent.name not in protected_agents:
            return None  # Allow agent to proceed

        # Read validation result once for logging / debugging
        validation_result = self._get_validation_result(callback_context)
        print(f"[RubricGuardrail] before_agent_callback - agent={agent.name}, validation_result={validation_result}")

        # If rubric is valid, allow the agent to proceed
        if validation_result and validation_result.get("status") == "valid":
            if agent.name == "ParallelGraders":
                self._ensure_dynamic_graders(agent, callback_context)
            print(f"[RubricGuardrail] ALLOW agent '{agent.name}' (rubric valid)")
            return None

        # Block the agent by returning Content
        self._blocked_agents.add(agent.name)
        logging.warning(
            "[RubricGuardrail] BLOCKED agent '%s' - rubric not valid.",
            agent.name,
        )
        print(f"[RubricGuardrail] BLOCK agent '{agent.name}' (rubric invalid or missing)")

        # Return Content to skip the agent (ADK pattern)
        return types.Content(
            role="model",
            parts=[types.Part(text=self._build_block_message(agent.name, callback_context))],
        )

# =============================================================================
# HUMAN-IN-THE-LOOP TOOL
# Concept: Day 2 - Long-running operations (pause/resume agents)
# =============================================================================

def request_grade_approval(
    final_score: float,
    max_score: float,
    percentage: float,
    letter_grade: str,
    reason: str,
    grade_summary: str,
    tool_context: ToolContext
) -> dict:
    """Request human approval for edge case grades.
    
    This tool pauses the agent and requests teacher confirmation
    for grades that are either failing (<50%) or exceptional (>90%).
    
    Args:
        final_score: The calculated final score
        max_score: Maximum possible score
        percentage: Score as percentage
        letter_grade: Letter grade (A, B, C, D, F)
        reason: Why approval is needed
        grade_summary: Summary of all criterion grades
        tool_context: ADK tool context for confirmation flow
    
    Returns:
        Approval status and message
    """
    
    # SCENARIO 1: First call - request confirmation
    if not tool_context.tool_confirmation:
        tool_context.request_confirmation(
            hint=f"""
⚠️ GRADE APPROVAL REQUIRED

Final Score: {final_score}/{max_score} ({percentage}%) - Grade: {letter_grade}

Reason: {reason}

Grade Summary:
{grade_summary}

Do you approve this grade?
            """,
            payload={
                "final_score": final_score,
                "percentage": percentage,
                "letter_grade": letter_grade,
            },
        )
        return {
            "status": "pending",
            "message": f"Awaiting teacher approval for grade {letter_grade} ({percentage}%)",
        }
    
    # SCENARIO 2: Resumed - handle approval response
    if tool_context.tool_confirmation.confirmed:
        return {
            "status": "approved",
            "approved_by": "human",
            "message": f"Grade {letter_grade} ({percentage}%) has been APPROVED by teacher",
        }
    else:
        return {
            "status": "rejected",
            "message": f"Grade {letter_grade} ({percentage}%) was REJECTED by teacher. Please review.",
        }


print("✅ Human-in-the-Loop tool defined")

# =============================================================================
# AGENT 1: RUBRIC VALIDATOR
# Concept: Day 1 - Single Agent with Tools
# =============================================================================

rubric_validator_agent = LlmAgent(
    name="RubricValidatorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Validates the structure and completeness of grading rubrics",
    instruction="""You are a rubric validation specialist. Your job is to validate 
    grading rubrics before they are used for evaluation.

    When you receive a rubric:
    1. Use the validate_rubric tool to check its structure.
    2. If valid, clearly confirm that the rubric is ready and list the criteria in a friendly way.
    3. If invalid, provide user-friendly error handling:
       - Start with a short, clear message that the rubric is not ready for grading.
       - List the specific problems in a structured way (bulleted list or numbered list).
       - For each problem, explain exactly what the teacher needs to change in the rubric.
       - End by saying explicitly that grading will NOT proceed until the rubric is fixed and validated again.

    Your tone should be professional, clear, and encouraging. Assume the user is a teacher who may not be technical.
    Always be precise and helpful in your feedback.""",
    tools=[validate_rubric],
    output_key="validation_result",
)

print("✅ RubricValidatorAgent created")

# =============================================================================
# AGENT 2: CRITERION GRADERS (Created dynamically based on rubric)
# Concept: Day 1 - Parallel Agents
# =============================================================================


def create_criterion_grader(criterion_name: str, criterion_description: str, max_score: int) -> LlmAgent:
    """Factory function to create a grader agent for a specific criterion.
    
    This allows us to create parallel graders dynamically based on the rubric.
    """
    criterion_slug = slugify(criterion_name)
    return LlmAgent(
        name=f"Grader_{criterion_slug}",
        model=Gemini(model=MODEL, retry_options=retry_config),
        description=f"Evaluates submissions for: {criterion_name}",
        instruction=f"""You are an expert evaluator for the criterion: "{criterion_name}"
        
        Criterion Description: {criterion_description}
        Maximum Score: {max_score} points
        
        When evaluating a submission:
        1. Carefully read the submission content
        2. Evaluate it against this specific criterion
        3. Determine a score from 0 to {max_score}
        4. Use the grade_criterion tool to record your evaluation
        5. Provide detailed justification for your score
        
        Be fair, consistent, and constructive in your feedback.
        Focus ONLY on this criterion - other aspects will be evaluated by other agents.""",
        tools=[grade_criterion],
        output_key=f"grade_{criterion_slug}",
    )


# Default graders for Python code rubric (dynamic pipeline will replace when rubric provided)
code_quality_grader = create_criterion_grader(
    "Code Quality", 
    "Evaluate code readability, naming conventions, and PEP 8 adherence",
    30
)

functionality_grader = create_criterion_grader(
    "Functionality",
    "Evaluate if the code correctly solves the problem",
    40
)

documentation_grader = create_criterion_grader(
    "Documentation",
    "Evaluate docstrings, comments, and code explanation",
    30
)

DEFAULT_GRADE_OUTPUT_KEYS = [
    code_quality_grader.output_key,
    functionality_grader.output_key,
    documentation_grader.output_key,
]

# Parallel agent to run all graders simultaneously
parallel_graders = ParallelAgent(
    name="ParallelGraders",
    sub_agents=[code_quality_grader, functionality_grader, documentation_grader],
)

print("✅ ParallelGraders created (3 criterion graders)")


def build_graders_from_rubric(rubric: dict) -> Tuple[List[LlmAgent], List[str]]:
    """Build grader agents and their output keys from rubric criteria."""
    graders: List[LlmAgent] = []
    grade_keys: List[str] = []
    criteria = rubric.get("criteria") or []
    for criterion in criteria:
        name = criterion.get("name") or "Unnamed Criterion"
        desc = criterion.get("description") or "No description provided"
        max_score = criterion.get("max_score") or 0
        slug = criterion.get("slug") or slugify(name)
        try:
            graders.append(create_criterion_grader(name, desc, max_score))
            grade_keys.append(f"grade_{slug}")
        except Exception as exc:
            logging.warning("Failed to create grader for criterion '%s': %s", name, exc)
    return graders, grade_keys

# =============================================================================
# AGENT 3: SCORE AGGREGATOR
# Concept: Day 1 - Sequential Agent coordination
# =============================================================================

aggregator_agent = LlmAgent(
    name="AggregatorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Aggregates individual criterion grades into a final score",
    instruction=f"""You are a grade aggregator. Your job is to:
    
    1. Collect all the individual criterion grades from the previous evaluation step
    2. Use the calculate_final_score tool to compute the final grade
    3. Summarize the evaluation results
    
    Session state references:
    - `grader_output_keys`: list created by the guardrail when a rubric is validated. Each entry is the key of a grade dict (e.g., grade_teamwork).
    - `rubric`: the validated rubric, where each criterion has a `name`, `max_score`, and `slug`.
    - If `grader_output_keys` is missing, fall back to the default keys: {", ".join(DEFAULT_GRADE_OUTPUT_KEYS)}.
    
    Workflow:
    1. First, call the build_grades_payload tool. It will read `grader_output_keys`,
       the rubric, and each grade_<slug> entry from session state, and return a
       JSON string in the `grades_json` field that is already in the format
       required by calculate_final_score.
    2. Then, call calculate_final_score using the `grades_json` value returned
       by build_grades_payload.
    3. After calculating, report:
       - Final score, percentage, and letter grade
       - Whether human approval is required (and why)
       - Summary of strengths and areas for improvement, referencing the individual grades.
    """,
    tools=[build_grades_payload, calculate_final_score],
    output_key="aggregation_result",
)

print("✅ AggregatorAgent created")

# =============================================================================
# AGENT 4: APPROVAL HANDLER
# Concept: Day 2 - Human-in-the-Loop (pause/resume)
# =============================================================================

approval_agent = LlmAgent(
    name="ApprovalAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Handles human approval for edge case grades",
    instruction="""You are the approval coordinator. Your job is to:
    
    1. Check if the aggregation result requires human approval
    2. If approval is needed (score < 50% or > 90%), use request_grade_approval tool
    3. If no approval needed, confirm the grade is finalized
    
    Read the aggregation_result from session state to get:
    - Final score and percentage
    - Whether approval is required
    - The reason for approval
    
    Be clear and professional in your communication.""",
    tools=[FunctionTool(request_grade_approval)],
    output_key="approval_result",
)

print("✅ ApprovalAgent created")

# =============================================================================
# AGENT 5: FEEDBACK GENERATOR
# Concept: Day 1 - Final agent in sequence
# =============================================================================

feedback_agent = LlmAgent(
    name="FeedbackGeneratorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Generates comprehensive feedback for the student",
    instruction="""You are a feedback specialist. Your job is to create 
    constructive, encouraging feedback for the student.
    
    Based on all the evaluation data in the session state:
    1. Start with positive aspects (what the student did well)
    2. Identify specific areas for improvement
    3. Provide actionable suggestions
    4. End with encouragement
    
    Your feedback should be:
    - Specific (reference actual parts of the submission)
    - Constructive (focus on improvement, not criticism)
    - Encouraging (motivate continued learning)
    - Clear (easy for the student to understand)
    
    Format your feedback in a clear, readable structure.""",
    output_key="final_feedback",
)

print("✅ FeedbackGeneratorAgent created")

# =============================================================================
# ROOT AGENT: ORCHESTRATOR
# Concept: Day 1 - Sequential Agent combining all steps
# =============================================================================

grading_pipeline = SequentialAgent(
    name="GradingPipeline",
    description="Executes the grading workflow: parallel grading -> aggregation -> approval -> feedback",
    sub_agents=[
        parallel_graders,
        aggregator_agent,
        approval_agent,
        feedback_agent,
    ],
)

print("✅ GradingPipeline created (without validator)")

# Root agent that coordinates the entire process
# Architecture: Root -> (1) Validate Rubric -> (2) If valid, run GradingPipeline
root_agent = LlmAgent(
    name="SmartGradingAssistant",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Main coordinator for the Smart Grading Assistant",
    instruction="""You are the Smart Grading Assistant, an AI-powered system 
    for evaluating academic submissions.
    
    **IMPORTANT WORKFLOW:**
    When a user provides a submission and rubric, you MUST follow this exact order:
    
    1. FIRST: Use the RubricValidatorAgent to validate the rubric structure
    2. CHECK the validation result:
       - If the rubric is VALID (status="valid"): proceed to step 3
       - If the rubric is INVALID: STOP HERE. Explain the errors to the user and ask them to fix the rubric. DO NOT proceed to grading.
    3. ONLY IF VALID: Delegate to the GradingPipeline for evaluation
    4. Present the final results clearly
    
    **GUARDRAIL:** Never call GradingPipeline if the rubric validation failed.
    This is a strict gate - invalid rubrics must be fixed before grading can proceed.
    
    If the user insists on grading with an invalid rubric, politely explain that
    the system requires a valid rubric to ensure fair and accurate evaluation.
    
    Be professional, helpful, and thorough in your responses.""",
    sub_agents=[rubric_validator_agent, grading_pipeline],
)

print("✅ Root Agent (SmartGradingAssistant) created")
print("   Architecture: Root -> Validate -> (if valid) -> GradingPipeline")

# =============================================================================
# APP CONFIGURATION
# Concept: Day 2 - Resumability for Human-in-the-Loop
# =============================================================================

grading_app = App(
    name=APP_NAME,
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
    plugins=[
        LoggingPlugin(),          # Observability: logs for all agents/tools/LLM calls
        RubricGuardrailPlugin(),  # Guardrail: backup safety - blocks if rubric not validated
    ],
)

print("✅ Resumable App configured")

# =============================================================================
# SESSION & RUNNER SETUP
# Concept: Day 3 - DatabaseSessionService for persistence
# =============================================================================

# Use SQLite for persistent sessions (stored under capstone/data)
db_path = os.path.join(DATA_DIR, "grading_sessions.db")
db_url = f"sqlite:///{db_path}"
session_service = DatabaseSessionService(db_url=db_url)

# Create runner with DatabaseSessionService (plugins attached to App)
runner = Runner(
    app=grading_app,
    session_service=session_service,
)

print("✅ Runner created with DatabaseSessionService")
print(f"   Database: {db_path}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def grade_submission(
    submission: str,
    rubric: dict,
    session_id: str = None
) -> dict:
    """Main function to grade a submission.
    
    Args:
        submission: The student's submission text
        rubric: The grading rubric as a dictionary
        session_id: Optional session ID for persistence
    
    Returns:
        Dictionary with grading results
    """
    if session_id is None:
        session_id = f"grading_{uuid.uuid4().hex[:8]}"
    
    # Create session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
    except:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
    
    # Prepare the grading request
    rubric_json = json.dumps(rubric, indent=2)
    query = f"""Please evaluate the following submission using the provided rubric.

RUBRIC:
{rubric_json}

SUBMISSION:
{submission}

Please proceed with the evaluation."""

    query_content = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    
    # Run the grading pipeline
    results = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=query_content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    results.append(part.text)
    
    return {
        "session_id": session_id,
        "results": results,
    }


async def demo():
    """Demo function to test the grading system."""
    
    print("\n" + "=" * 60)
    print("🎓 SMART GRADING ASSISTANT - DEMO")
    print("=" * 60)
    
    # Load sample rubric from capstone/examples
    rubric_path = os.path.join(BASE_DIR, "examples", "rubrics", "python_code_rubric.json")
    with open(rubric_path, "r") as f:
        rubric = json.load(f)
    
    # Load sample submission from capstone/examples
    submission_path = os.path.join(BASE_DIR, "examples", "submissions", "sample_code.py")
    with open(submission_path, "r") as f:
        submission = f.read()
    
    print(f"\n📋 Rubric: {rubric['name']}")
    print(f"📝 Submission: Fibonacci Calculator")
    print("\n⏳ Starting evaluation...\n")
    
    result = await grade_submission(submission, rubric)
    
    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)
    
    for text in result["results"]:
        if text and text.strip():
            print(f"\n{text}")
    
    print("\n" + "=" * 60)
    print(f"✅ Session ID: {result['session_id']}")
    print("=" * 60)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("\n🚀 Starting Smart Grading Assistant...")
    asyncio.run(demo())
