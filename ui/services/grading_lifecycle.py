"""Grading lifecycle management - runner, app, and session lifecycle."""

import streamlit as st

try:
    from agent import grading_app, runner as _default_runner, create_grading_runner
    from google.genai import types

    ADK_AVAILABLE = True
except Exception:
    ADK_AVAILABLE = False
    grading_app = None
    _default_runner = None
    create_grading_runner = None
    types = None


# Backwards-compatible public runner attribute
runner = _default_runner

def invalidate_runner() -> None:
    """Drop cached runner/app so a new one is created on next access.
    
    Also clears approval/resume state to prevent attempting to resume
    with a different runner instance.
    """
    if "_adk_runner" in st.session_state:
        del st.session_state["_adk_runner"]
    if "_adk_app" in st.session_state:
        del st.session_state["_adk_app"]
    if "_adk_provider" in st.session_state:
        del st.session_state["_adk_provider"]
    
    # Clear approval/resume state to prevent cross-runner contamination
    st.session_state.last_invocation_id = None
    st.session_state.approval_decision = None
    st.session_state.pending_approval = False
    st.session_state.requested_tool_confirmations = None


def get_app():
    """Get the cached App instance from session state."""
    if not ADK_AVAILABLE:
        return None
    if "_adk_app" not in st.session_state:
        get_runner()
    return st.session_state.get("_adk_app")


def get_runner():
    """Get or create runner instance stored in Streamlit session state.
    
    This ensures the same runner (with InMemorySessionService) persists
    across Streamlit reruns, solving the session loss problem during approval flow.
    """
    if not ADK_AVAILABLE:
        return None

    provider = st.session_state.get("llm_provider", "gemini")

    # If a runner was provided externally (e.g. overridden at runtime/tests), prefer it.
    if runner is not None and runner is not _default_runner:
        st.session_state["_adk_runner"] = runner
        st.session_state["_adk_app"] = grading_app
        st.session_state["_adk_provider"] = provider
        return st.session_state.get("_adk_runner")

    # Cache hit: same provider, reuse runner
    if (
        st.session_state.get("_adk_runner") is not None
        and st.session_state.get("_adk_provider") == provider
    ):
        return st.session_state.get("_adk_runner")

    # Cache miss or provider changed: invalidate and recreate
    invalidate_runner()

    if create_grading_runner is None:
        # Fallback to default runner if factory not available
        st.session_state["_adk_runner"] = runner
        st.session_state["_adk_app"] = grading_app
    else:
        # Use factory to create runner with selected provider
        new_runner, new_app = create_grading_runner(provider=provider)
        st.session_state["_adk_runner"] = new_runner
        st.session_state["_adk_app"] = new_app

    st.session_state["_adk_provider"] = provider
    return st.session_state.get("_adk_runner")


def start_grading_session() -> str:
    """Create or resume an ADK grading session.
    
    Returns:
        Session ID string
    """
    import uuid
    
    # Generate a new session ID if not exists
    if not st.session_state.grading_session_id:
        session_id = str(uuid.uuid4())
        st.session_state.grading_session_id = session_id
    
    return st.session_state.grading_session_id
