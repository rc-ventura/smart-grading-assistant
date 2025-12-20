"""Grading service - Bridge between Streamlit UI and ADK grading backend.

This module provides functions to interact with the ADK grading pipeline,
including session management, rubric validation, and grading execution.
"""

import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Generator

import streamlit as st

from ui.services.grading_mapper import map_runner_event
from ui.services.grading_runner import (
    run_runner_events as run_runner_events_impl, 
    resume_runner_with_confirmation
)

try:
    from agent import grading_app, runner as _default_runner
    from google.genai import types

    ADK_AVAILABLE = True
except Exception:
    ADK_AVAILABLE = False
    grading_app = None
    _default_runner = None
    types = None


def get_runner():
    """Get or create runner instance stored in Streamlit session state.
    
    This ensures the same runner (with InMemorySessionService) persists
    across Streamlit reruns, solving the session loss problem during approval flow.
    """
    if not ADK_AVAILABLE:
        return None
    
    # Initialize runner in session state if not present
    if '_adk_runner' not in st.session_state:
        st.session_state._adk_runner = _default_runner
    
    return st.session_state._adk_runner


def start_grading_session() -> str:
    """Create or resume an ADK grading session.
    
    Returns:
        Session ID string
    """
    # Generate a new session ID if not exists
    if not st.session_state.grading_session_id:
        session_id = str(uuid.uuid4())
        st.session_state.grading_session_id = session_id
    
    return st.session_state.grading_session_id


def send_rubric(rubric_json: str) -> dict[str, Any]:
    """Send rubric to backend for validation.
    
    Args:
        rubric_json: JSON string containing the rubric
        
    Returns:
        Validation result dict with 'valid', 'errors', and 'criteria_count'
    """
    try:
        rubric = json.loads(rubric_json)
        
        # Basic validation (mirrors backend RubricValidatorAgent logic)
        errors = []
        
        if not isinstance(rubric, dict):
            errors.append("Rubric must be a JSON object")
        else:
            if "name" not in rubric:
                errors.append("Missing required field: 'name'")
            
            criteria = rubric.get("criteria", [])
            if not criteria:
                errors.append("Missing or empty 'criteria' array")
            else:
                total_points = 0
                for i, c in enumerate(criteria):
                    if "name" not in c:
                        errors.append(f"Criterion {i+1} missing 'name'")
                    if "max_score" not in c:
                        errors.append(f"Criterion {i+1} missing 'max_score'")
                    elif c.get("max_score", 0) <= 0:
                        errors.append(f"Criterion {i+1} 'max_score' must be positive")
                    else:
                        total_points += c.get("max_score", 0)
                    if "description" not in c:
                        errors.append(f"Criterion {i+1} missing 'description'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "criteria_count": len(rubric.get("criteria", [])),
            "total_points": total_points if not errors else 0,
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON: {str(e)}"],
            "criteria_count": 0,
            "total_points": 0,
        }


def send_submission(submission_text: str) -> dict[str, Any]:
    """Store submission in session state for grading.
    
    Args:
        submission_text: The student submission text
        
    Returns:
        Confirmation dict with 'stored', 'length', and 'preview'
    """
    if not submission_text or not submission_text.strip():
        return {
            "stored": False,
            "error": "Submission cannot be empty",
            "length": 0,
            "preview": "",
        }
    
    st.session_state.submission_text = submission_text
    
    return {
        "stored": True,
        "length": len(submission_text),
        "preview": submission_text[:200] + "..." if len(submission_text) > 200 else submission_text,
    }


async def run_runner_events(rubric_json: str, submission_text: str) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator: send rubric and submission to ADK Runner and yield raw events."""
    runner = get_runner()
    async for event in run_runner_events_impl(
        rubric_json,
        submission_text,
        runner=runner,
        grading_app=grading_app,
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
    if not runner:
        yield {
            "type": "error",
            "step": "runner",
            "data": {"message": "ADK backend not available"},
        }
        return
#TODO Fix it the event_loop persistence. The loop must not persist outside where it was created. (improves.md#event-loop-persistence)
    loop = st.session_state.get("_adk_event_loop")
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        st.session_state["_adk_event_loop"] = loop
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
                grading_app=grading_app,
                types=types
            ))
        else:
            # Explicitly call impl with dependencies
            runner = get_runner()
            agen = _consume_and_yield(run_runner_events_impl(
                rubric_json, 
                submission_text,
                runner=runner,
                grading_app=grading_app,
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
        try:
            if agen is not None:
                loop.run_until_complete(agen.aclose())
        except Exception:
            pass
        try:
            asyncio.set_event_loop(None)
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


def is_adk_available() -> bool:
    """Check if ADK backend is available.
    
    Returns:
        True if ADK is importable and configured
    """
    return ADK_AVAILABLE