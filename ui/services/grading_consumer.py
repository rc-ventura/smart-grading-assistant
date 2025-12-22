import json
import streamlit as st
from ui.components.chat import add_message, render_chat
from ui.services.grading import run_grading


def consume_grading_events(chat_slot, results_slot) -> None:
   
    if st.session_state.get("cancel_requested"):
        st.session_state.cancel_requested = False
        st.session_state.grading_in_progress = False
        st.session_state.current_step = "idle"
        st.session_state.pending_approval = False
        st.session_state.approval_decision = None
        add_message("assistant", "🛑 Grading cancelled by user.")
        st.rerun()

    def _event_key(event: dict) -> str:
        event_type = event.get("type", "")
        step = event.get("step", "")
        data = event.get("data", {})

        if event_type in {"step_start", "step_complete"}:
            return f"{event_type}:{step}"

        if event_type == "criterion_graded":
            if isinstance(data, dict):
                criterion = data.get("criterion_name") or data.get("criterion") or "unknown"
            else:
                criterion = "unknown"
            return f"{event_type}:{criterion}"

        if event_type == "grading_complete":
            return "grading_complete"

        if event_type == "error":
            msg = ""
            if isinstance(data, dict):
                msg = data.get("message", "")
            return f"{event_type}:{step}:{msg}"

        try:
            payload = json.dumps(
                {"type": event_type, "step": step, "data": data},
                sort_keys=True,
                default=str,
            )
            return payload
        except Exception:
            return f"{event_type}:{step}:{repr(data)}"

    try:
        for event in run_grading():
            if st.session_state.get("cancel_requested"):
                st.session_state.cancel_requested = False
                st.session_state.grading_in_progress = False
                st.session_state.current_step = "idle"
                st.session_state.pending_approval = False
                st.session_state.approval_decision = None
                add_message("assistant", "🛑 Grading cancelled by user.")
                break

            event_type = event.get("type", "")
            step = event.get("step", "")
            data = event.get("data", {})

            if "event_log" in st.session_state:
                event_log = st.session_state.event_log
                index = st.session_state.get("_event_log_index")
                if not isinstance(index, dict):
                    index = {}
                    st.session_state._event_log_index = index

                key = _event_key(event)
                if key not in index:
                    index[key] = len(event_log)
                    event_log.append(event)

            if event_type == "step_start":
                st.session_state.current_step = step
                seen = st.session_state.get("_seen_step_start")
                if not isinstance(seen, dict):
                    seen = {}
                    st.session_state._seen_step_start = seen
                if step not in seen:
                    seen[step] = True
                    add_message("assistant", f"📋 {data.get('message', step)}")

            elif event_type == "step_complete":
                seen = st.session_state.get("_seen_step_complete")
                if not isinstance(seen, dict):
                    seen = {}
                    st.session_state._seen_step_complete = seen
                if step in seen:
                    pass
                else:
                    seen[step] = True
                    if step == "validating":
                        add_message(
                            "assistant",
                            f"✅ {data.get('message', 'Rubric validated successfully')}",
                        )
                    elif step == "grading":
                        add_message("assistant", f"✅ {data.get('message', 'Step complete')}")
                    elif step == "aggregating":
                        st.session_state.final_score = data
                        score = data.get("percentage", 0)
                        grade = data.get("letter_grade", "N/A")
                        add_message("assistant", f"📊 Final Score: {score:.1f}% ({grade})")
                    elif step == "feedback":
                        st.session_state.feedback = data
                        add_message("assistant", "💬 Feedback generated!")

            elif event_type == "criterion_graded":
                criterion = data.get("criterion_name", "Unknown")
                st.session_state.grades[criterion] = data

                seen = st.session_state.get("_seen_criteria")
                if not isinstance(seen, dict):
                    seen = {}
                    st.session_state._seen_criteria = seen

                if criterion not in seen:
                    seen[criterion] = True
                    score = data.get("score", 0)
                    max_score = data.get("max_score", 0)
                    notes = (
                        data.get("evaluation_notes")
                        or data.get("justification")
                        or ""
                    )
                    if isinstance(notes, str) and len(notes) > 140:
                        notes = notes[:140].rstrip() + "..."
                    if notes:
                        add_message(
                            "assistant",
                            f"✅ **{criterion}**: {score:.1f}/{max_score:.0f}\n\n_{notes}_",
                        )
                    else:
                        add_message(
                            "assistant",
                            f"✅ **{criterion}**: {score:.1f}/{max_score:.0f}",
                        )

            elif event_type == "error":
                st.session_state.error_message = data.get("message", "Unknown error")
                add_message("assistant", f"❌ Error: {st.session_state.error_message}")
                st.session_state.grading_in_progress = False
                st.session_state.current_step = "idle"
                break

            elif event_type == "grading_complete":
                st.session_state.current_step = "complete"
                add_message("assistant", "✅ Grading complete! Review the results below.")

            elif event_type == "approval_finalized":
                data = event.get("data", {})
                msg = data.get("message", "Grade finalized.")
                add_message("assistant", f"🛡️ **Approval Processed:** {msg}")

            if st.session_state.get("pending_approval") and not st.session_state.get(
                "_pending_approval_notified"
            ):
                st.session_state._pending_approval_notified = True
                reason = st.session_state.get("approval_reason") or "Edge case detected"
                add_message("assistant", f"⚠️ **Approval Required:** {reason}")

            with chat_slot.container():
                render_chat()

        st.session_state.grading_in_progress = False

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.grading_in_progress = False
        st.session_state.current_step = "idle"
        add_message("assistant", f"❌ Error during grading: {e}")

    st.rerun()
