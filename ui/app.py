import sys
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types

# Ensure project root is on sys.path so `capstone` package is importable
UI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = UI_DIR.parent  # /capstone
REPO_ROOT = PROJECT_ROOT.parent  # repo root

for path in (str(PROJECT_ROOT), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Grading Assistant",
    page_icon="📝",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# Gemini Client Initialization
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
if "genai_client" not in st.session_state:
    st.session_state.genai_client = genai.Client(api_key=GEMINI_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialization (from spec)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_STATE = {
    # Setup flags
    "setup_complete": False,
    # Rubric state
    "rubric_json": None,
    "rubric_valid": False,
    "rubric_errors": [],
    # Submission state
    "submission_text": None,
    # Grading session state
    "grading_session_id": None,
    "grading_in_progress": False,
    "current_step": "idle",  # idle, validating, grading, aggregating, feedback, complete
    # Results state
    "grades": {},
    "final_score": None,
    "feedback": None,
    # Chat/messages state
    "messages": [],
    # Human-in-the-loop state
    "pending_approval": False,
    "approval_reason": None,
    # Error state
    "error_message": None,
}

for key, default_value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────
def reset_session():
    """Clear all session state and restart."""
    for key in DEFAULT_STATE:
        st.session_state[key] = DEFAULT_STATE[key]
    st.rerun()


def start_grading():
    """Trigger the grading process and run the pipeline."""
    from ui.services.grading import start_grading_session
    from ui.components.chat import add_message
    
    st.session_state.messages = []
    st.session_state.grading_session_id = None
    st.session_state.grades = {}
    st.session_state.final_score = None
    st.session_state.feedback = None
    st.session_state.pending_approval = False
    st.session_state.approval_reason = None
    st.session_state.error_message = None
    st.session_state.current_step = "idle"
    
    # Initialize session
    start_grading_session()
    st.session_state.grading_in_progress = True
    st.session_state.error_message = None
    
    # Add start message
    add_message("assistant", "🚀 Starting grading process...")


def _consume_grading_events(chat_slot, results_slot) -> None:
    from ui.components.chat import add_message, render_chat
    from ui.components.results import render_results
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
            with results_slot.container():
                render_results()

        st.session_state.grading_in_progress = False

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.grading_in_progress = False
        st.session_state.current_step = "idle"
        add_message("assistant", f"❌ Error during grading: {e}")

    with chat_slot.container():
        render_chat()
    with results_slot.container():
        render_results()


# ─────────────────────────────────────────────────────────────────────────────
# Main Layout
# ─────────────────────────────────────────────────────────────────────────────
st.title("📝 Smart Grading Assistant")

# Import components
from ui.components.sidebar import render_sidebar
from ui.components.chat import render_chat, add_message, add_grading_update
from ui.components.results import render_results
from ui.services.grading import (
    start_grading_session,
    run_grading,
    get_results,
)

# Render sidebar with callbacks
with st.sidebar:
    render_sidebar(
        on_start_grading=start_grading,
        on_reset=reset_session,
    )

# Main area - chat/grading interface and results
main_area = st.container()
with main_area:
    chat_slot = st.empty()
    results_slot = st.empty()
    debug_slot = st.empty()

    with chat_slot.container():
        render_chat()

    with results_slot.container():
        render_results()

    if st.session_state.grading_in_progress:
        _consume_grading_events(chat_slot, results_slot)

    with debug_slot.container():
        with st.expander("Debug: Session State", expanded=False):
            st.json({
                "setup_complete": st.session_state.setup_complete,
                "rubric_valid": st.session_state.rubric_valid,
                "submission_loaded": st.session_state.submission_text is not None,
                "current_step": st.session_state.current_step,
                "grading_in_progress": st.session_state.grading_in_progress,
                "grades": st.session_state.grades,
                "final_score": st.session_state.final_score,
            })