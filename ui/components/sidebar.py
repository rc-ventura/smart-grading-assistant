"""Sidebar component for rubric and submission setup."""

import json
from typing import Callable

import streamlit as st


def render_sidebar(
    on_start_grading: Callable[[], None],
    on_reset: Callable[[], None],
) -> None:
    """Render the sidebar with rubric/submission inputs and actions.
    
    Args:
        on_start_grading: Callback when "Start Grading" is clicked
        on_reset: Callback when "Reset" is clicked
    """
    st.header("📋 Setup")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Rubric Input Section
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("Rubric")
    
    rubric_tab_upload, rubric_tab_paste = st.tabs(["📁 Upload", "📝 Paste"])
    
    with rubric_tab_upload:
        rubric_file = st.file_uploader(
            "Upload rubric JSON",
            type=["json"],
            key="rubric_file_uploader",
            help="Upload a JSON file containing the grading rubric",
        )
        if rubric_file is not None:
            _process_rubric_file(rubric_file)
    
    with rubric_tab_paste:
        rubric_text = st.text_area(
            "Paste rubric JSON",
            height=150,
            key="rubric_text_area",
            placeholder='{"name": "My Rubric", "criteria": [...]}',
            help="Paste your rubric JSON directly",
        )
        if rubric_text:
            _process_rubric_text(rubric_text)
    
    # Show rubric validation status
    if st.session_state.rubric_json:
        if st.session_state.rubric_valid:
            st.success("✅ Rubric is valid")
            with st.expander("Preview rubric", expanded=False):
                try:
                    rubric_data = json.loads(st.session_state.rubric_json)
                    st.write(f"**Name:** {rubric_data.get('name', 'Unnamed')}")
                    criteria = rubric_data.get("criteria", [])
                    st.write(f"**Criteria:** {len(criteria)}")
                    for c in criteria:
                        st.write(f"- {c.get('name', 'Unknown')} ({c.get('max_score', 0)} pts)")
                except json.JSONDecodeError:
                    st.write("Unable to preview")
        else:
            st.error("❌ Rubric is invalid")
            if st.session_state.rubric_errors:
                for error in st.session_state.rubric_errors:
                    st.write(f"- {error}")
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Submission Input Section
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("Submission")
    
    submission_tab_upload, submission_tab_paste = st.tabs(["📁 Upload", "📝 Paste"])
    
    with submission_tab_upload:
        submission_file = st.file_uploader(
            "Upload submission",
            type=["py", "txt", "md"],
            key="submission_file_uploader",
            help="Upload a .py, .txt, or .md file",
        )
        if submission_file is not None:
            _process_submission_file(submission_file)
    
    with submission_tab_paste:
        submission_text = st.text_area(
            "Paste submission",
            height=150,
            key="submission_text_area",
            placeholder="Paste student code or text here...",
            help="Paste the student submission directly",
        )
        if submission_text:
            st.session_state.submission_text = submission_text
    
    # Show submission status
    if st.session_state.submission_text:
        text_len = len(st.session_state.submission_text)
        st.success(f"✅ Submission loaded ({text_len} chars)")
        with st.expander("Preview submission", expanded=False):
            preview = st.session_state.submission_text[:500]
            if len(st.session_state.submission_text) > 500:
                preview += "\n... (truncated)"
            st.code(preview, language="python")
    else:
        st.warning("⚠️ No submission loaded")
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Quick Actions
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("Actions")
    
    # Determine if grading can start
    can_start = (
        st.session_state.rubric_valid 
        and st.session_state.submission_text is not None
        and not st.session_state.grading_in_progress
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.button(
            "🚀 Start Grading",
            on_click=on_start_grading,
            disabled=not can_start,
            type="primary",
            use_container_width=True,
        )
    
    with col2:
        st.button(
            "🔄 Reset",
            on_click=on_reset,
            type="secondary",
            use_container_width=True,
        )
    
    if not can_start and not st.session_state.grading_in_progress:
        if not st.session_state.rubric_valid:
            st.caption("⚠️ Load a valid rubric to enable grading")
        elif st.session_state.submission_text is None:
            st.caption("⚠️ Load a submission to enable grading")
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Session Info
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("Session Info")
    
    # Current step indicator
    step = st.session_state.current_step
    step_icons = {
        "idle": "⏸️",
        "validating": "🔍",
        "grading": "📊",
        "aggregating": "🧮",
        "feedback": "💬",
        "complete": "✅",
    }
    st.write(f"**Step:** {step_icons.get(step, '❓')} {step.capitalize()}")
    
    # Session ID
    if st.session_state.grading_session_id:
        st.write(f"**Session ID:** `{st.session_state.grading_session_id[:12]}...`")
    else:
        st.write("**Session ID:** Not started")
    
    # Grading progress
    if st.session_state.grading_in_progress:
        st.info("🔄 Grading in progress...")


def _process_rubric_file(file) -> None:
    """Process uploaded rubric file."""
    try:
        content = file.read().decode("utf-8")
        _validate_and_store_rubric(content)
    except Exception as e:
        st.session_state.rubric_json = None
        st.session_state.rubric_valid = False
        st.session_state.rubric_errors = [f"Failed to read file: {str(e)}"]


def _process_rubric_text(text: str) -> None:
    """Process pasted rubric text."""
    _validate_and_store_rubric(text)


def _validate_and_store_rubric(json_str: str) -> None:
    """Validate rubric JSON and store in session state."""
    errors = []
    
    try:
        rubric = json.loads(json_str)
        
        # Basic validation
        if not isinstance(rubric, dict):
            errors.append("Rubric must be a JSON object")
        else:
            if "name" not in rubric:
                errors.append("Missing required field: 'name'")
            
            if "criteria" not in rubric:
                errors.append("Missing required field: 'criteria'")
            elif not isinstance(rubric.get("criteria"), list):
                errors.append("'criteria' must be an array")
            elif len(rubric.get("criteria", [])) == 0:
                errors.append("'criteria' must have at least one item")
            else:
                for i, criterion in enumerate(rubric["criteria"]):
                    if not isinstance(criterion, dict):
                        errors.append(f"Criterion {i+1} must be an object")
                        continue
                    if "name" not in criterion:
                        errors.append(f"Criterion {i+1} missing 'name'")
                    if "max_score" not in criterion:
                        errors.append(f"Criterion {i+1} missing 'max_score'")
                    elif not isinstance(criterion.get("max_score"), (int, float)):
                        errors.append(f"Criterion {i+1} 'max_score' must be a number")
                    elif criterion.get("max_score", 0) <= 0:
                        errors.append(f"Criterion {i+1} 'max_score' must be positive")
                    if "description" not in criterion:
                        errors.append(f"Criterion {i+1} missing 'description'")
        
        st.session_state.rubric_json = json_str
        st.session_state.rubric_valid = len(errors) == 0
        st.session_state.rubric_errors = errors
        
    except json.JSONDecodeError as e:
        st.session_state.rubric_json = json_str
        st.session_state.rubric_valid = False
        st.session_state.rubric_errors = [f"Invalid JSON: {str(e)}"]


def _process_submission_file(file) -> None:
    """Process uploaded submission file."""
    try:
        content = file.read().decode("utf-8")
        st.session_state.submission_text = content
    except Exception as e:
        st.session_state.submission_text = None
        st.error(f"Failed to read file: {str(e)}")
