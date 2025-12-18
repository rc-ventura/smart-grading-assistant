from typing import Any

import streamlit as st


def map_runner_event(raw_event: Any) -> dict[str, Any]:
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
                    if (
                        "requires_approval" not in aggregation
                        and "requires_human_approval" in aggregation
                    ):
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
                    getattr(p, "text", None) for p in parts if getattr(p, "text", None)
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
