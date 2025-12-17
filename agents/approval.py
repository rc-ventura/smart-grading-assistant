"""Approval Agent - handles human-in-the-loop for edge case grades."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from services.llm_provider import get_model, get_agent_generate_config
from config import MODEL_LITE, retry_config


def finalize_grade(
    final_score: float,
    max_score: float,
    percentage: float,
    letter_grade: str,
    reason: str,
    tool_context: ToolContext | None = None,
) -> dict:
    """Finalize and record the grade. Requires human confirmation.
    
    Args:
        final_score: The calculated final score
        max_score: Maximum possible score  
        percentage: Score as percentage
        letter_grade: Letter grade (A, B, C, D, F)
        reason: Why this grade was given
    
    Returns:
        Confirmation that grade was finalized
    """
    return {
        "status": "finalized",
        "final_score": final_score,
        "max_score": max_score,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "reason": reason,
        "message": f"Grade {letter_grade} ({percentage}%) has been finalized.",
    }


async def needs_approval(
    final_score: float,
    max_score: float,
    percentage: float,
    letter_grade: str,
    reason: str,
    tool_context: ToolContext | None = None,
) -> bool:
    """Returns True if the grade requires human approval."""

    if tool_context is not None:
        try:
            aggregation_result = tool_context.state.get("aggregation_result")
        except Exception:
            aggregation_result = None

        if isinstance(aggregation_result, dict):
            if aggregation_result.get("requires_human_approval") is True:
                return True

            if aggregation_result.get("failed_criteria") or aggregation_result.get("missing_grade_keys"):
                return True

    return percentage < 50 or percentage > 90


approval_agent = LlmAgent(
    name="ApprovalAgent",
    model=get_model(),
    generate_content_config=get_agent_generate_config(),
    description="Handles human approval for edge case grades",
    instruction="""You finalize grades. 
    
    Read the aggregation_result from session state (saved by AggregatorAgent).
    Call finalize_grade ONCE with the values from aggregation_result.
    
    The system will automatically request human confirmation if the grade is an edge case.
    After calling finalize_grade, do NOT generate additional text.""",
    tools=[FunctionTool(finalize_grade, require_confirmation=needs_approval)],
    output_key="approval_result",
)

print("✅ ApprovalAgent created")
