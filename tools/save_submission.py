"""Tool to persist the student's submission text in session state.

This allows other agents (e.g., feedback or debugging tools) to
access the original submission from the ToolContext state.
"""

from google.adk.tools.tool_context import ToolContext


def save_submission(submission_content: str, tool_context: ToolContext) -> dict:
    """Save the student's submission text into session state.

    Args:
        submission_content: Full text of the student's submission.
        tool_context: ADK ToolContext providing access to session state.

    Returns:
        Dict with basic metadata about the stored submission.
    """
    if not submission_content or not submission_content.strip():
        return {
            "status": "error",
            "error_message": "Submission content cannot be empty.",
        }

    # Persist the raw submission so downstream agents can reference it
    try:
        tool_context.state["submission_text"] = submission_content
    except Exception:
        # Best-effort: do not break the flow if state is not writable
        return {
            "status": "error",
            "error_message": "Failed to write submission to session state.",
        }

    preview = submission_content[:200]
    if len(submission_content) > 200:
        preview += "..."

    return {
        "status": "stored",
        "length": len(submission_content),
        "preview": preview,
    }
