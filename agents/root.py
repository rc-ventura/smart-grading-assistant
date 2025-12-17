"""Root Agent - orchestrates the entire grading workflow."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool

from config import MODEL_LITE, retry_config
from tools.save_submission import save_submission
from tools.validate_rubric import validate_rubric
from .graders import parallel_graders
from .aggregator import aggregator_agent
from .approval import approval_agent
from .feedback import feedback_agent


# Grading Pipeline: combines all grading steps
grading_pipeline = SequentialAgent(
    name="GradingPipeline",
    description="Executes the complete grading workflow: evaluates each criterion, aggregates scores, handles approval, and generates feedback.",
    sub_agents=[
        parallel_graders,
        aggregator_agent,
        approval_agent,
        feedback_agent,
    ],
)

print("✅ GradingPipeline created")

# Root Agent: hybrid design
# - validate_rubric and save_submission are direct tools (root controls)
# - GradingPipeline is a sub-agent (transfer_to_agent for real execution)
root_agent = LlmAgent(
    name="SmartGradingAssistant",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Main coordinator for the Smart Grading Assistant",
    instruction="""You are the Smart Grading Assistant. You control rubric validation and submission storage directly, then delegate grading to a specialized pipeline.

    TOOLS AVAILABLE:
    - validate_rubric: Validates a grading rubric (JSON format). This is a GATE - you cannot grade without a valid rubric.
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

    RULES:
    - NEVER transfer to GradingPipeline without a valid rubric.
    - NEVER transfer to GradingPipeline without a saved submission.
    - Respond in the user's language.
    - Be helpful and guide the user through the process.""",
    tools=[
        FunctionTool(validate_rubric),
        FunctionTool(save_submission),
    ],
    sub_agents=[grading_pipeline],
)

print("✅ Root Agent (SmartGradingAssistant) created")
print("   Design: Hybrid - tools for validation/submission, sub-agent for grading pipeline")

