"""
Tool for finalizing and recording grades with human approval.
"""

from config.settings import FAILING_THRESHOLD, EXCEPTIONAL_THRESHOLD
from google.adk.tools.tool_context import ToolContext


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
    # Check if already finalized to avoid double approval
    if tool_context is not None:
        try:
            existing_approval = tool_context.state.get("approval_result")
            if existing_approval is not None:
                # Already approved, just return the existing result
                return existing_approval
        except Exception:
            pass
    
    result = {
        "status": "finalized",
        "final_score": final_score,
        "max_score": max_score,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "reason": reason,
        "message": f"Grade {letter_grade} ({percentage}%) has been finalized.",
    }
    
    # Store in state for future checks
    if tool_context is not None:
        try:
            tool_context.state["approval_result"] = result
        except Exception:
            pass
    
    return result


async def needs_approval(
    final_score: float,
    max_score: float,
    percentage: float,
    letter_grade: str,
    reason: str,
    tool_context: ToolContext | None = None,
) -> bool:
    """Returns True if the grade requires human approval."""

    # If already approved/finalized in this ADK session context, do not ask again.
    if tool_context is not None:
        try:
            if tool_context.state.get("approval_result") is not None:
                return False
        except Exception:
            pass

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

    return percentage < FAILING_THRESHOLD or percentage > EXCEPTIONAL_THRESHOLD
