import copy
import streamlit as st
from google import genai
from google.genai import types
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
    "event_log": [],
    "_event_log_index": {},
    "_seen_step_start": {},
    "_seen_step_complete": {},
    "_seen_criteria": {},
    "_pending_approval_notified": False,
    # Human-in-the-loop state
    "pending_approval": False,
    "approval_reason": None,
    "requested_tool_confirmations": None,
    # Error state
    "error_message": None,
}

for key, default_value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = copy.deepcopy(default_value)


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────
def reset_session():
    """Clear all session state and restart."""
    for key, default_value in DEFAULT_STATE.items():
        st.session_state[key] = copy.deepcopy(default_value)
    st.rerun()


def start_grading():
    """Trigger the grading process and run the pipeline."""
    from ui.services.grading import start_grading_session
    from ui.components.chat import add_message
    
    st.session_state.messages = []
    st.session_state.event_log = []
    st.session_state._event_log_index = {}
    st.session_state._seen_step_start = {}
    st.session_state._seen_step_complete = {}
    st.session_state._seen_criteria = {}
    st.session_state._pending_approval_notified = False
    st.session_state.grading_session_id = None
    st.session_state.grades = {}
    st.session_state.final_score = None
    st.session_state.feedback = None
    st.session_state.pending_approval = False
    st.session_state.approval_reason = None
    st.session_state.requested_tool_confirmations = None
    st.session_state.error_message = None
    st.session_state.current_step = "idle"
    
    # Initialize session
    start_grading_session()
    st.session_state.grading_in_progress = True
    st.session_state.error_message = None
    
    # Add start message
    add_message("assistant", "🚀 Starting grading process...")


# ─────────────────────────────────────────────────────────────────────────────
# Main Layout
# ─────────────────────────────────────────────────────────────────────────────
st.title("📝 Smart Grading Assistant")

# Import components
from ui.components.sidebar import render_sidebar
from ui.components.chat import render_chat
from ui.components.results import render_results, render_reports
from ui.services.grading_consumer import consume_grading_events


# Render sidebar with callbacks
with st.sidebar:
    render_sidebar(
        on_start_grading=start_grading,
        on_reset=reset_session,
    )

# Main area - chat/grading interface and results
main_area = st.container()
with main_area:
    tab_chat, tab_results, tab_debug, tab_reports = st.tabs(
        ["Chat", "Results", "Debug", "Reports"]
    )

    with tab_chat:
        chat_slot = st.empty()

    with tab_results:
        results_slot = st.empty()

    with tab_debug:
        debug_slot = st.empty()

    with tab_reports:
        reports_slot = st.empty()

    with tab_results:
        with results_slot.container():
            render_results()

    with tab_reports:
        with reports_slot.container():
            render_reports()

    with tab_debug:
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

    if st.session_state.grading_in_progress:
        with tab_chat:
            consume_grading_events(chat_slot, results_slot)
    else:
        with tab_chat:
            with chat_slot.container():
                render_chat()