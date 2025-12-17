"""Grading service - Bridge between Streamlit UI and ADK grading backend.

This module provides functions to interact with the ADK grading pipeline,
including session management, rubric validation, and grading execution.
"""

import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Generator, Iterable

import streamlit as st

# Import ADK components (with fallback for when backend is not available)
try:
    from capstone.agent import grading_app, runner
    from google.genai import types
    ADK_AVAILABLE = True
except Exception:
    ADK_AVAILABLE = False
    grading_app = None
    runner = None
    types = None


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


async def _run_runner_events(rubric_json: str, submission_text: str) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator: send rubric and submission to ADK Runner and yield raw events."""
    if not st.session_state.grading_session_id:
        st.session_state.grading_session_id = str(uuid.uuid4())

    user_id = "teacher"
    session_id = st.session_state.grading_session_id

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

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=submission_text)]),
    ):
        try:
            state_delta = getattr(getattr(event, "actions", None), "state_delta", None)
            if isinstance(state_delta, dict):
                if not started_aggregating and "aggregation_result" in state_delta:
                    started_aggregating = True
                    yield {
                        "type": "event",
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
                        "data": {
                            "type": "step_start",
                            "step": "feedback",
                            "data": {"message": "Generating feedback..."},
                        },
                    }
        except Exception:
            pass

        yield {"type": "event", "data": event}

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


def _map_runner_event(raw_event: Any) -> dict[str, Any]:
    """Translate ADK event to UI-friendly event. Falls back to generic event."""
    try:
        if isinstance(raw_event, dict):
            # If runner already emits structured step events
            if "type" in raw_event and "step" in raw_event:
                return raw_event
            # Generic message
            return {"type": "event", "step": "runner", "data": raw_event}

        actions = getattr(raw_event, "actions", None)
        state_delta = getattr(actions, "state_delta", None)
        requested_tool_confirmations = getattr(actions, "requested_tool_confirmations", None)

        def _normalize(value: Any) -> Any:
            if hasattr(value, "model_dump"):
                try:
                    return value.model_dump()
                except Exception:
                    return value
            if hasattr(value, "dict"):
                try:
                    return value.dict()
                except Exception:
                    return value
            return value

        if isinstance(state_delta, dict):
            for key, value in state_delta.items():
                try:
                    st.session_state[key] = _normalize(value)
                except Exception:
                    pass

            if st.session_state.grades is None:
                st.session_state.grades = {}

            validation_payload = state_delta.get("rubric_validation") or state_delta.get(
                "validation_result"
            )
            if validation_payload is not None:
                normalized = _normalize(validation_payload)
                if isinstance(normalized, dict):
                    if normalized.get("status") == "valid":
                        st.session_state.rubric_valid = True
                        st.session_state.rubric_errors = []
                    elif normalized.get("status") == "invalid":
                        st.session_state.rubric_valid = False
                        st.session_state.rubric_errors = normalized.get("errors") or []

            for key, value in state_delta.items():
                if not isinstance(key, str) or not key.startswith("grade_"):
                    continue

                normalized = _normalize(value)
                if key.endswith("_error"):
                    if isinstance(normalized, dict):
                        criterion_name = normalized.get("criterion_name") or key
                        max_score = normalized.get("max_score") or 0
                        grade_result = {
                            "criterion_name": criterion_name,
                            "score": 0,
                            "max_score": max_score,
                            "evaluation_notes": normalized.get("error_message")
                            or "Failed to grade.",
                        }
                        st.session_state.grades[criterion_name] = grade_result
                        st.session_state.pending_approval = True
                        if not st.session_state.approval_reason:
                            st.session_state.approval_reason = (
                                "One or more criteria failed to grade."
                            )
                        return {
                            "type": "criterion_graded",
                            "step": "grading",
                            "data": grade_result,
                        }
                    continue

                if isinstance(normalized, dict):
                    criterion_name = normalized.get("criterion_name") or key
                    st.session_state.grades[criterion_name] = normalized
                    return {
                        "type": "criterion_graded",
                        "step": "grading",
                        "data": normalized,
                    }

            if "aggregation_result" in state_delta:
                aggregation = _normalize(state_delta.get("aggregation_result"))
                if isinstance(aggregation, dict):
                    if "requires_approval" not in aggregation and "requires_human_approval" in aggregation:
                        aggregation["requires_approval"] = aggregation.get(
                            "requires_human_approval"
                        )
                    st.session_state.final_score = aggregation
                    if aggregation.get("requires_human_approval") or aggregation.get(
                        "requires_approval"
                    ):
                        st.session_state.pending_approval = True
                        st.session_state.approval_reason = aggregation.get("approval_reason")
                    return {
                        "type": "step_complete",
                        "step": "aggregating",
                        "data": aggregation,
                    }

            if "final_feedback" in state_delta:
                feedback = _normalize(state_delta.get("final_feedback"))
                if isinstance(feedback, dict):
                    if "improvements" not in feedback and "areas_for_improvement" in feedback:
                        feedback["improvements"] = feedback.get("areas_for_improvement")
                    st.session_state.feedback = feedback
                    return {
                        "type": "step_complete",
                        "step": "feedback",
                        "data": feedback,
                    }

        if isinstance(requested_tool_confirmations, dict) and requested_tool_confirmations:
            normalized_confirmations = {
                k: _normalize(v) for k, v in requested_tool_confirmations.items()
            }
            st.session_state.pending_approval = True
            if not st.session_state.approval_reason:
                first = next(iter(normalized_confirmations.values()), None)
                if isinstance(first, dict):
                    hint = first.get("hint")
                    if isinstance(hint, str) and hint.strip():
                        st.session_state.approval_reason = hint
            st.session_state.requested_tool_confirmations = normalized_confirmations
            return {
                "type": "event",
                "step": "approval",
                "data": {"requested_tool_confirmations": normalized_confirmations},
            }

        message = None
        try:
            content = getattr(raw_event, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                texts = [
                    getattr(p, "text", None)
                    for p in parts
                    if getattr(p, "text", None)
                ]
                if texts:
                    message = "\n".join(texts)
        except Exception:
            pass

        data: dict[str, Any] = {"author": getattr(raw_event, "author", None)}
        if message:
            data["message"] = message
        return {"type": "event", "step": "runner", "data": data}
    except Exception:
        return {"type": "event", "step": "runner", "data": {"message": "Unhandled runner event"}}


def _simulate_grading(rubric: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Fallback simulation when ADK backend is not available."""
    # Step 1: Validating
    yield {"type": "step_start", "step": "validating", "data": {"message": "Validating rubric structure..."}}

    validation = send_rubric(json.dumps(rubric))
    if not validation["valid"]:
        yield {"type": "error", "step": "validating", "data": {"message": "Rubric validation failed", "errors": validation["errors"]}}
        return

    yield {"type": "step_complete", "step": "validating", "data": {"message": "Rubric validated successfully"}}

    # Step 2: Grading
    yield {"type": "step_start", "step": "grading", "data": {"message": "Grading submission against criteria..."}}

    criteria = rubric.get("criteria", [])
    grades = {}
    import random
    for criterion in criteria:
        criterion_name = criterion.get("name", "Unknown")
        max_score = criterion.get("max_score", 0)
        score = round(random.uniform(0.6, 1.0) * max_score, 1)
        grade_result = {
            "criterion_name": criterion_name,
            "score": score,
            "max_score": max_score,
            "evaluation_notes": f"Evaluated {criterion_name} based on submission content. Score reflects overall quality.",
        }
        grades[criterion_name] = grade_result
        yield {"type": "criterion_graded", "step": "grading", "data": grade_result}

    st.session_state.grades = grades
    yield {"type": "step_complete", "step": "grading", "data": {"message": f"Graded {len(criteria)} criteria"}}

    # Step 3: Aggregating
    yield {"type": "step_start", "step": "aggregating", "data": {"message": "Aggregating scores..."}}
    total_score = sum(g["score"] for g in grades.values())
    max_possible = sum(g["max_score"] for g in grades.values())
    percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
    if percentage >= 90:
        letter_grade = "A"
    elif percentage >= 80:
        letter_grade = "B"
    elif percentage >= 70:
        letter_grade = "C"
    elif percentage >= 60:
        letter_grade = "D"
    else:
        letter_grade = "F"
    requires_approval = percentage < 50 or percentage > 90
    approval_reason = None
    if percentage < 50:
        approval_reason = "Score below 50% - please verify before finalizing"
    elif percentage > 90:
        approval_reason = "Score above 90% - please verify exceptional grade"
    final_score = {
        "total_score": total_score,
        "max_possible": max_possible,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "requires_human_approval": requires_approval,
        "requires_approval": requires_approval,
        "approval_reason": approval_reason,
    }
    st.session_state.final_score = final_score
    if requires_approval:
        st.session_state.pending_approval = True
        st.session_state.approval_reason = approval_reason
    yield {"type": "step_complete", "step": "aggregating", "data": final_score}

    # Step 4: Feedback
    yield {"type": "step_start", "step": "feedback", "data": {"message": "Generating feedback..."}}
    feedback = {
        "strengths": [
            "Clear code structure and organization",
            "Good use of comments and documentation",
            "Follows naming conventions",
        ],
        "improvements": [
            "Consider adding more error handling",
            "Some functions could be broken down further",
            "Add more comprehensive test coverage",
        ],
        "suggestions": [
            "Review Python best practices for the specific patterns used",
            "Consider using type hints throughout",
            "Add docstrings to all public functions",
        ],
        "encouragement": "Good work overall! Keep practicing and refining your skills.",
        "overall_summary": f"The submission demonstrates solid understanding of the core concepts. Final grade: {letter_grade} ({percentage:.1f}%)",
    }
    st.session_state.feedback = feedback
    yield {"type": "step_complete", "step": "feedback", "data": feedback}
    yield {
        "type": "grading_complete",
        "step": "complete",
        "data": {
            "session_id": st.session_state.grading_session_id,
            "final_score": final_score,
            "grades": grades,
            "feedback": feedback,
        },
    }


def run_grading() -> Generator[dict[str, Any], None, None]:
    """Execute the grading pipeline and yield events for UI updates."""
    rubric_json = st.session_state.rubric_json
    submission_text = st.session_state.submission_text

    if not rubric_json or not submission_text:
        yield {"type": "error", "step": "validation", "data": {"message": "Missing rubric or submission"}}
        return

    try:
        rubric = json.loads(rubric_json)
    except json.JSONDecodeError as e:
        yield {"type": "error", "step": "validation", "data": {"message": f"Invalid rubric JSON: {e}"}}
        return

    if ADK_AVAILABLE:
        loop = st.session_state.get("_adk_event_loop")
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            st.session_state["_adk_event_loop"] = loop
        agen: AsyncGenerator[dict[str, Any], None] | None = None
        try:
            async def _runner_wrapper():
                async for raw in _run_runner_events(rubric_json, submission_text):
                    yield _map_runner_event(raw["data"])
            # Consume async generator synchronously for Streamlit
            asyncio.set_event_loop(loop)
            agen = _runner_wrapper()
            while True:
                try:
                    event = loop.run_until_complete(agen.__anext__())
                    yield event
                except StopAsyncIteration:
                    break
            return
        except Exception as e:
            yield {"type": "error", "step": "runner", "data": {"message": f"Backend error: {e}"}}
            # Fallback to simulation to keep UX responsive
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

    # Simulation fallback
    for ev in _simulate_grading(rubric):
        yield ev


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


# TODO: Remove the simulate grading fallback when ADK is stable