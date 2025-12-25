"""Grading execution - running the grading pipeline and handling events."""

import asyncio
import json
from typing import Any, AsyncGenerator, Generator

import streamlit as st

from ui.services.grading_mapper import map_runner_event
from ui.services.grading_runner import (
    run_runner_events as run_runner_events_impl, 
    resume_runner_with_confirmation
)
from ui.services.grading_lifecycle import get_runner, get_app, reset_grading_state

try:
    from google.genai import types
    ADK_AVAILABLE = True
except Exception:
    types = None
    ADK_AVAILABLE = False


async def run_runner_events(rubric_json: str, submission_text: str) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator: send rubric and submission to ADK Runner and yield raw events."""
    runner = get_runner()
    app = get_app()
    async for event in run_runner_events_impl(
        rubric_json,
        submission_text,
        runner=runner,
        grading_app=app,
        types=types,
    ):
        yield event


def run_grading() -> Generator[dict[str, Any], None, None]:
    """Execute the grading pipeline and yield events for UI updates."""
    # Clean transient state for a new run 
    if not st.session_state.get("grading_in_progress"):
        reset_grading_state()
    st.session_state.grading_in_progress = True

    rubric_json = st.session_state.rubric_json
    submission_text = st.session_state.submission_text

    if not rubric_json or not submission_text:
        yield {"type": "error", "step": "validation", "data": {"message": "Missing rubric or submission"}}
        return

    try:
        json.loads(rubric_json)
    except json.JSONDecodeError as e:
        yield {"type": "error", "step": "validation", "data": {"message": f"Invalid rubric JSON: {e}"}}
        return

    runner = get_runner()
    app = get_app()
    if not runner:
        st.session_state.grading_in_progress = False
        st.session_state.grades = {}
        st.session_state.final_score = None
        st.session_state.feedback = None
        st.session_state.current_step = "idle"
        yield {
            "type": "error",
            "step": "runner",
            "data": {"message": "ADK backend not available"},
        }
        return
    
    approval_decision = st.session_state.get("approval_decision")

    if approval_decision == "manual_adjust":
        yield {
            "type": "approval_action",
            "step": "approval",
            "data": {
                "action": "manual_adjust",
                "final_score": st.session_state.get("manual_final_score"),
                "letter_grade": st.session_state.get("manual_letter_grade"),
            },
        }

        manual_final_score = st.session_state.get("manual_final_score")
        manual_letter_grade = st.session_state.get("manual_letter_grade")
        manual_feedback = st.session_state.get("manual_feedback")

        base_final = st.session_state.get("final_score")
        max_possible = 100.0
        try:
            if isinstance(base_final, dict) and base_final.get("max_possible") is not None:
                max_possible = float(base_final.get("max_possible"))
        except Exception:
            pass

        try:
            total_score = float(manual_final_score) if manual_final_score is not None else 0.0
        except Exception:
            total_score = 0.0

        percentage = 0.0
        try:
            percentage = (total_score / max_possible * 100.0) if max_possible else 0.0
        except Exception:
            percentage = 0.0

        st.session_state.final_score = {
            "total_score": total_score,
            "max_possible": max_possible,
            "percentage": percentage,
            "letter_grade": (manual_letter_grade or "N/A"),
            "requires_human_approval": False,
            "requires_approval": False,
            "approval_reason": None,
        }

        st.session_state.feedback = {
            "overall_summary": manual_feedback if isinstance(manual_feedback, str) else ""
        }

        st.session_state.pending_approval = False
        st.session_state.requested_tool_confirmations = None
        st.session_state.last_invocation_id = None
        st.session_state.approval_decision = None
        st.session_state.approval_followup = None
        st.session_state.regrade_comment = ""
        st.session_state.grading_in_progress = False
        st.session_state.current_step = "complete"

        yield {
            "type": "grading_complete",
            "step": "complete",
            "data": {
                "session_id": st.session_state.grading_session_id,
                "final_score": st.session_state.final_score,
                "grades": st.session_state.grades,
                "feedback": st.session_state.feedback,
            },
        }
        return

    if approval_decision == "regrade":
        yield {
            "type": "approval_action",
            "step": "approval",
            "data": {"action": "regrade"},
        }

        st.session_state.pending_approval = False
        st.session_state.requested_tool_confirmations = None
        st.session_state.last_invocation_id = None
        st.session_state.approval_decision = None
        st.session_state.approval_reason = None
        st.session_state._pending_approval_notified = False
        st.session_state.approval_followup = None
        st.session_state.regrade_comment = ""

        st.session_state.grades = {}
        st.session_state.final_score = None
        st.session_state.feedback = None
        st.session_state.current_step = "idle"

        st.session_state.grading_session_id = None

        # Inform UI that a new cycle is starting.
        yield {
            "type": "step_start",
            "step": "regrade",
            "data": {"message": "Regrading requested. Restarting the grading cycle..."},
        }

    if approval_decision == "cancelled":
        yield {
            "type": "approval_action",
            "step": "approval",
            "data": {"action": "cancelled"},
        }

        st.session_state.grading_in_progress = False
        st.session_state.pending_approval = False
        st.session_state.requested_tool_confirmations = None
        st.session_state.last_invocation_id = None
        st.session_state.approval_decision = None
        st.session_state.current_step = "idle"
        return

    # Create event loop locally (not persisted in session_state)
    loop = asyncio.new_event_loop()
    agen: AsyncGenerator[dict[str, Any], None] | None = None
    
    try:
        async def _consume_and_yield(generator):
            async for raw in generator:
                # Capture invocation_id if present
                if "invocation_id" in raw:
                    st.session_state.last_invocation_id = raw["invocation_id"]
                
                # Yield mapped event
                if "data" in raw:
                     yield map_runner_event(raw["data"])
                else:
                     yield map_runner_event(raw)

        invocation_id = st.session_state.get("last_invocation_id")
        requested_confirmations = st.session_state.get("requested_tool_confirmations")

        if approval_decision and invocation_id and requested_confirmations:
            yield {
                "type": "approval_action",
                "step": "approval",
                "data": {
                    "action": "approved" if approval_decision == "approved" else approval_decision,
                },
            }

            # Build FunctionResponse for each requested confirmation
            function_responses = []
            for call_id, confirmation_details in requested_confirmations.items():
                # Extract the actual function call ID (remove any prefix)
                actual_call_id = call_id
                
                # Create FunctionResponse with adk_request_confirmation
                func_response = types.FunctionResponse(
                    name="adk_request_confirmation",
                    id=actual_call_id,
                    response={
                        "confirmed": approval_decision == "approved"
                    }
                )
                function_responses.append(func_response)
            
            # Prevent re-sending the same confirmation on rerun
            st.session_state.requested_tool_confirmations = None
            st.session_state.pending_approval = False

            # Create Content with FunctionResponse parts
            msg = types.Content(
                role="user",
                parts=[types.Part(function_response=fr) for fr in function_responses]
            )
            
            agen = _consume_and_yield(resume_runner_with_confirmation(
                invocation_id,
                msg,
                runner=runner,
                grading_app=app,
                types=types
            ))
        else:
            # Explicitly call impl with dependencies
            runner = get_runner()
            agen = _consume_and_yield(run_runner_events_impl(
                rubric_json, 
                submission_text,
                runner=runner,
                grading_app=app,
                types=types
            ))

        # Consume async generator synchronously for Streamlit
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                event = loop.run_until_complete(agen.__anext__())
                yield event
            except StopAsyncIteration:
                break
        return
    except Exception as e:
        # Safe reset for recoverable errors 
        reset_grading_state()
        yield {"type": "error", "step": "runner", "data": {"message": f"Backend error: {e}"}}
        return
    finally:
        # Proper cleanup: close async generator, shutdown async generators, close loop
        try:
            if agen is not None:
                loop.run_until_complete(agen.aclose())
        except Exception:
            pass
        
        try:
            # Shutdown any pending async generators
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
        
        try:
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass


def get_results() -> dict[str, Any]:
    """Fetch final grading results from session state.
    
    Returns:
        Dict with grades, final_score, and feedback
    """
    return {
        "session_id": st.session_state.grading_session_id,
        "grades": st.session_state.grades,
        "final_score": st.session_state.final_score,
        "feedback": st.session_state.feedback,
        "rubric": st.session_state.rubric_json,
        "submission_preview": (
            st.session_state.submission_text[:500] + "..."
            if st.session_state.submission_text and len(st.session_state.submission_text) > 500
            else st.session_state.submission_text
        ),
    }
