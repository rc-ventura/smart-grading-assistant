import uuid
from typing import Any, AsyncGenerator

import streamlit as st
from ui.services.grading_lifecycle import invalidate_runner, reset_grading_state


async def run_runner_events(
    rubric_json: str,
    submission_text: str,
    *,
    runner: Any,
    grading_app: Any,
    types: Any,
) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator: send rubric and submission to ADK Runner and yield raw events."""
    if not st.session_state.grading_session_id:
        st.session_state.grading_session_id = str(uuid.uuid4())

    user_id = "teacher"
    session_id = st.session_state.grading_session_id

    try:
        session = await runner.session_service.get_session(
            app_name=grading_app.name,
            user_id=user_id,
            session_id=session_id,
        )
        if session is None:
            session = await runner.session_service.create_session(
                app_name=grading_app.name,
                user_id=user_id,
                session_id=session_id,
            )
    except Exception as e:
        # Backend closed or session service unavailable: reset and ask user to retry
        invalidate_runner()
        reset_grading_state()
        yield {
            "type": "event",
            "data": {
                "type": "error",
                "step": "runner",
                "data": {"message": f"Backend closed or unavailable: {e}. Session was reset; please retry."},
            },
        }
        return

    st.session_state.grading_session_id = session.id

    yield {
        "type": "event",
        "data": {
            "type": "step_start",
            "step": "validating",
            "data": {"message": "Validating rubric structure..."},
        },
    }

    rubric_validation: dict[str, Any] | None = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=rubric_json)]),
    ):
        try:
            state_delta = getattr(getattr(event, "actions", None), "state_delta", None)
            if isinstance(state_delta, dict):
                candidate = state_delta.get("rubric_validation") or state_delta.get(
                    "validation_result"
                )
                if isinstance(candidate, dict):
                    rubric_validation = candidate
        except Exception:
            pass
        yield {"type": "event", "data": event}

    if isinstance(rubric_validation, dict) and rubric_validation.get("status") != "valid":
        yield {
            "type": "event",
            "data": {
                "type": "error",
                "step": "validating",
                "data": {
                    "message": "Rubric validation failed",
                    "errors": rubric_validation.get("errors") or [],
                },
            },
        }
        return

    yield {
        "type": "event",
        "data": {
            "type": "step_complete",
            "step": "validating",
            "data": {"message": "Rubric validated successfully"},
        },
    }
    yield {
        "type": "event",
        "data": {
            "type": "step_start",
            "step": "grading",
            "data": {"message": "Grading submission against criteria..."},
        },
    }

    started_aggregating = False
    started_feedback = False

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=submission_text)]),
        ):
            invocation_id = getattr(event, "invocation_id", None)
            
            try:
                state_delta = getattr(getattr(event, "actions", None), "state_delta", None)
                if isinstance(state_delta, dict):
                    if not started_aggregating and "aggregation_result" in state_delta:
                        started_aggregating = True
                        yield {
                            "type": "event",
                            "invocation_id": invocation_id,
                            "data": {
                                "type": "step_start",
                                "step": "aggregating",
                                "data": {"message": "Aggregating scores..."},
                            },
                        }
                    if not started_feedback and "final_feedback" in state_delta:
                        started_feedback = True
                        yield {
                            "type": "event",
                            "invocation_id": invocation_id,
                            "data": {
                                "type": "step_start",
                                "step": "feedback",
                                "data": {"message": "Generating feedback..."},
                            },
                        }
            except Exception:
                pass

            yield {
                "type": "event", 
                "invocation_id": invocation_id,
                "data": event
            }
    except Exception as e:
        invalidate_runner()
        reset_grading_state()
        yield {
            "type": "event",
            "data": {
                "type": "error",
                "step": "runner",
                "data": {"message": f"Backend error during grading: {e}. Session was reset; please retry."},
            },
        }
        return

    # If we are pending approval, do NOT yield completion event
    if st.session_state.get("pending_approval"):
        return

    # Clear approval state after successful resume
    st.session_state.approval_reason = None
    st.session_state.requested_tool_confirmations = None
    st.session_state.last_invocation_id = None
    st.session_state.approval_decision = None

    yield {
        "type": "event",
        "data": {
            "type": "grading_complete",
            "step": "complete",
            "data": {
                "session_id": st.session_state.grading_session_id,
                "final_score": st.session_state.final_score,
                "grades": st.session_state.grades,
                "feedback": st.session_state.feedback,
            },
        },
    }


async def resume_runner_with_confirmation(
    invocation_id: str,
    confirmation_message: Any,
    *,
    runner: Any,
    grading_app: Any,
    types: Any,
) -> AsyncGenerator[dict[str, Any], None]:
    """Resume runner with confirmation response."""
    if not st.session_state.grading_session_id:
        return

    user_id = "teacher"
    session_id = st.session_state.grading_session_id

    # We assume session exists
    
    yield {
        "type": "event",
        "data": {
            "type": "step_start",
            "step": "resuming",
            "data": {"message": "Resuming with approval..."},
        },
    }

    started_aggregating = False
    started_feedback = False

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        invocation_id=invocation_id,
        new_message=confirmation_message,
    ):
        invocation_id = getattr(event, "invocation_id", None)

        try:
            state_delta = getattr(getattr(event, "actions", None), "state_delta", None)
            if isinstance(state_delta, dict):
                if not started_aggregating and "aggregation_result" in state_delta:
                    started_aggregating = True
                    yield {
                        "type": "event",
                        "invocation_id": invocation_id,
                        "data": {
                            "type": "step_start",
                            "step": "aggregating",
                            "data": {"message": "Aggregating scores..."},
                        },
                    }
                if not started_feedback and "final_feedback" in state_delta:
                    started_feedback = True
                    yield {
                        "type": "event",
                        "invocation_id": invocation_id,
                        "data": {
                            "type": "step_start",
                            "step": "feedback",
                            "data": {"message": "Generating feedback..."},
                        },
                    }
        except Exception:
            pass

        yield {
            "type": "event", 
            "invocation_id": invocation_id,
            "data": event
        }

    # If we are pending approval, do NOT yield completion event
    if st.session_state.get("pending_approval"):
        return

    yield {
        "type": "event",
        "data": {
            "type": "grading_complete",
            "step": "complete",
            "data": {
                "session_id": st.session_state.grading_session_id,
                "final_score": st.session_state.final_score,
                "grades": st.session_state.grades,
                "feedback": st.session_state.feedback,
            },
        },
    }
