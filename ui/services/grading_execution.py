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
from ui.services.grading_lifecycle import get_runner, get_app

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
        yield {
            "type": "error",
            "step": "runner",
            "data": {"message": "ADK backend not available"},
        }
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

        approval_decision = st.session_state.get("approval_decision")
        invocation_id = st.session_state.get("last_invocation_id")

        if approval_decision and invocation_id:
            st.session_state.approval_decision = None
            
            msg = types.Content(role="user", parts=[types.Part(text=f"User decision: {approval_decision}")])
            
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
