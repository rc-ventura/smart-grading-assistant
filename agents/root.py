"""Root Agent - orchestrates the entire grading workflow."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool

from services.llm_provider import get_model, get_agent_generate_config
from .rubric_validator import rubric_validator_agent, create_rubric_validator_agent
from config import MODEL_LITE, MODEL, retry_config
from tools.save_submission import save_submission
from .graders import parallel_graders
from .aggregator import aggregator_agent, create_aggregator_agent
from .approval import approval_agent, create_approval_agent
from .feedback import feedback_agent, create_feedback_agent


def create_grading_pipeline(aggregator, approval, feedback, graders=None):
    """Factory function to create GradingPipeline with provided agents.
    
    Args:
        aggregator: Aggregator agent instance
        approval: Approval agent instance
        feedback: Feedback agent instance
        graders: Optional ParallelGraders agent. If None, uses default parallel_graders.
    """
    if graders is None:
        graders = parallel_graders
    
    return SequentialAgent(
        name="GradingPipeline",
        description="Executes the grading workflow with structured outputs.",
        sub_agents=[
            graders,
            aggregator,
            approval,
            feedback,
        ],
    )


def create_root_agent(model=None, rubric_validator=None, grading_pipeline_agent=None):
    """Factory function to create root agent with optional model and sub-agents."""
    if model is None:
        model = get_model()
    if rubric_validator is None:
        rubric_validator = rubric_validator_agent
    if grading_pipeline_agent is None:
        grading_pipeline_agent = grading_pipeline
    
    return LlmAgent(
        name="SmartGradingAssistant",
        model=model,
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
4. When received, call save_submission to store it (call it with no arguments; it reads the submission from the user's message).
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
            AgentTool(agent=rubric_validator),
            FunctionTool(save_submission),
        ],
        sub_agents=[grading_pipeline_agent]
    )


# Default singleton instances (backward compatibility)
grading_pipeline = create_grading_pipeline(
    aggregator_agent,
    approval_agent,
    feedback_agent,
)

print("✅ GradingPipeline created (SequentialAgent with structured outputs)")

root_agent = create_root_agent()

print("✅ Root Agent (SmartGradingAssistant) created")
print("   Design: Hybrid - tools for validation/submission, SequentialAgent for grading pipeline")

