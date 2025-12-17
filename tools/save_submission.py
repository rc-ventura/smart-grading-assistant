"""Tool to persist the student's submission text in session state.

This allows other agents (e.g., feedback or debugging tools) to
access the original submission from the ToolContext state.
"""

import json

from google.adk.tools.tool_context import ToolContext


def save_submission(tool_context: ToolContext) -> dict:
    """Save the student's submission text into session state.

    Args:
        tool_context: ADK ToolContext providing access to session state.

    Returns:
        Dict with basic metadata about the stored submission.
    """
    user_content = getattr(tool_context, "user_content", None)
    parts = getattr(user_content, "parts", None) if user_content else None
    if not parts:
        return {
            "status": "error",
            "error_message": "Submission content cannot be empty.",
        }

    raw_text = "\n".join(p.text for p in parts if getattr(p, "text", None))
    if not raw_text or not raw_text.strip():
        return {
            "status": "error",
            "error_message": "Submission content cannot be empty.",
        }

    submission_content = raw_text
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            candidate = parsed.get("submission")
            if isinstance(candidate, str):
                submission_content = candidate
            else:
                candidate = parsed.get("submission_text")
                if isinstance(candidate, str):
                    submission_content = candidate
    except Exception:
        pass

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
