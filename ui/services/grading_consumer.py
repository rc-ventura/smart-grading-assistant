import streamlit as st


def consume_grading_events(chat_slot, results_slot) -> None:
    from ui.components.chat import add_message, render_chat
    from ui.services.grading import run_grading

    try:
        for event in run_grading():
            event_type = event.get("type", "")
            step = event.get("step", "")
            data = event.get("data", {})

            if event_type == "step_start":
                st.session_state.current_step = step
                add_message("assistant", f"📋 {data.get('message', step)}")

            elif event_type == "step_complete":
                if step == "grading":
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

            elif event_type == "error":
                st.session_state.error_message = data.get("message", "Unknown error")
                add_message("assistant", f"❌ Error: {st.session_state.error_message}")
                st.session_state.grading_in_progress = False
                st.session_state.current_step = "idle"
                break

            elif event_type == "grading_complete":
                st.session_state.current_step = "complete"
                add_message("assistant", "✅ Grading complete! Review the results below.")

            with chat_slot.container():
                render_chat()

        st.session_state.grading_in_progress = False

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.grading_in_progress = False
        st.session_state.current_step = "idle"
        add_message("assistant", f"❌ Error during grading: {e}")

    st.rerun()
