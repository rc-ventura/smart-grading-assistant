"""Root Agent - orchestrates the entire grading workflow."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool

from services.gemini_client import get_model, get_agent_generate_config
from .rubric_validator import rubric_validator_agent
from config import MODEL_LITE, MODEL, retry_config
from tools.save_submission import save_submission
from .graders import parallel_graders
from .aggregator import aggregator_agent
from .approval import approval_agent
from .feedback import feedback_agent


# Grading Pipeline: Sequential execution with structured outputs
# Each agent now uses output_schema to guarantee valid JSON responses
# This prevents the "string instead of structured data" problem
grading_pipeline = SequentialAgent(
    name="GradingPipeline",
    description="Executes the grading workflow with structured outputs.",
    sub_agents=[
        parallel_graders,   # Graders use output_schema -> guaranteed JSON
        aggregator_agent,   # Reads structured grades from state
        approval_agent,     # Finalizes grade
        feedback_agent,     # Generates structured feedback
    ],
)

print("✅ GradingPipeline created (SequentialAgent with structured outputs)")

# Root Agent: hybrid design with better error handling
# - validate_rubric and save_submission are direct tools (root controls)
# - GradingPipeline is a sub-agent (transfer_to_agent for real execution)
root_agent = LlmAgent(
    name="SmartGradingAssistant",
    model=get_model(),
    generate_content_config=get_agent_generate_config(),
    description="Main coordinator for the Smart Grading Assistant",
    instruction="""You are the Smart Grading Assistant. You control rubric validation and submission storage directly, then delegate grading to a specialized pipeline.

TOOLS AVAILABLE:
- rubric_validator_agent: Validates a grading rubric (JSON format) call another agent tool. This is a GATE - you cannot grade without a valid rubric.
- save_submission: Saves the student's submission text for evaluation.

SUB-AGENT AVAILABLE:
- GradingPipeline: Use transfer_to_agent("GradingPipeline") to execute the full grading process.

WORKFLOW:
1. Ask the user for the RUBRIC (preferably JSON format).
2. When received, call validate_rubric to check it. If invalid, explain the errors and ask for corrections.
3. Once rubric is valid, ask the user for the STUDENT SUBMISSION.
4. When received, call save_submission to store it.
5. With both rubric valid AND submission saved, use transfer_to_agent("GradingPipeline") to execute the full evaluation.
6. After the pipeline completes, present the final results.

ERROR HANDLING:
- If any step fails, explain the error clearly and suggest how to fix it.
- The pipeline can retry failed steps automatically.
- If you receive an error from a tool, analyze it and decide whether to retry or ask the user for help.

RULES:
- NEVER transfer to GradingPipeline without a valid rubric.
- NEVER transfer to GradingPipeline without a saved submission.
- Respond in the user's language.
- Be helpful and guide the user through the process.""",
    tools=[
        AgentTool(agent=rubric_validator_agent),
        FunctionTool(save_submission),
    ],
    sub_agents=[grading_pipeline]
)

print("✅ Root Agent (SmartGradingAssistant) created")
print("   Design: Hybrid - tools for validation/submission, SequentialAgent for grading pipeline")

