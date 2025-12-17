"""Chat/grading interface component for displaying progress and messages."""

import streamlit as st


def render_chat() -> None:
    """Render the chat/grading interface with progress and messages."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # Progress Indicator
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.grading_in_progress or st.session_state.current_step != "idle":
        _render_progress_indicator()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chat History
    # ─────────────────────────────────────────────────────────────────────────
    _render_chat_history()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Per-Criterion Scores (as they complete)
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.grades:
        _render_criterion_scores()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Error Display
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.error_message:
        st.error(f"❌ Error: {st.session_state.error_message}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Input Box (optional teacher queries)
    # ─────────────────────────────────────────────────────────────────────────
    if not st.session_state.grading_in_progress and st.session_state.current_step == "idle":
        _render_input_box()


def _render_progress_indicator() -> None:
    """Render the current grading step progress."""
    step = st.session_state.current_step
    
    steps = ["validating", "grading", "aggregating", "feedback", "complete"]
    step_labels = {
        "idle": "Ready",
        "validating": "Validating Rubric",
        "grading": "Grading Criteria",
        "aggregating": "Aggregating Scores",
        "feedback": "Generating Feedback",
        "complete": "Complete",
    }
    
    # Calculate progress
    if step in steps:
        current_idx = steps.index(step)
        progress = (current_idx + 1) / len(steps)
    else:
        progress = 0
    
    # Show progress bar
    st.progress(progress, text=f"**{step_labels.get(step, step.capitalize())}**")
    
    # Show step details
    if st.session_state.grading_in_progress:
        with st.spinner(f"{step_labels.get(step, 'Processing')}..."):
            st.empty()


def _render_chat_history() -> None:
    """Render the chat message history."""
    messages = st.session_state.messages
    
    if not messages:
        st.info("👋 Upload a rubric and submission in the sidebar to get started.")
        return
    
    for message in messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        # Skip system messages
        if role == "system":
            continue
        
        with st.chat_message(role):
            st.markdown(content)


def _render_criterion_scores() -> None:
    """Render per-criterion scores as they complete."""
    grades = st.session_state.grades
    
    if not grades:
        return
    
    st.subheader("📊 Grading Progress")
    
    cols = st.columns(min(len(grades), 3))
    
    for idx, (criterion_name, grade_data) in enumerate(grades.items()):
        col_idx = idx % 3
        with cols[col_idx]:
            score = grade_data.get("score", 0)
            max_score = grade_data.get("max_score", 0)
            percentage = (score / max_score * 100) if max_score > 0 else 0
            
            # Color based on score
            if percentage >= 80:
                color = "🟢"
            elif percentage >= 60:
                color = "🟡"
            else:
                color = "🔴"
            
            st.metric(
                label=f"{color} {criterion_name}",
                value=f"{score:.1f}/{max_score:.0f}",
                delta=f"{percentage:.0f}%",
            )


def _render_input_box() -> None:
    """Render optional input box for teacher queries."""
    prompt = st.chat_input(
        "Ask a question about grading (optional)",
        key="chat_input",
    )
    
    if prompt:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })
        
        # Add placeholder assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": "I'll help you with that once grading is complete. Please upload a rubric and submission first.",
        })
        
        st.rerun()


def add_message(role: str, content: str) -> None:
    """Add a message to the chat history.
    
    Args:
        role: Message role ('user', 'assistant', 'system')
        content: Message content
    """
    st.session_state.messages.append({
        "role": role,
        "content": content,
    })


def add_grading_update(step: str, details: str = "") -> None:
    """Add a grading progress update message.
    
    Args:
        step: Current grading step
        details: Optional details about the step
    """
    step_messages = {
        "validating": "🔍 Validating rubric structure...",
        "grading": "📊 Grading submission against criteria...",
        "aggregating": "🧮 Aggregating scores...",
        "feedback": "💬 Generating feedback...",
        "complete": "✅ Grading complete!",
    }
    
    message = step_messages.get(step, f"Processing: {step}")
    if details:
        message += f"\n{details}"
    
    add_message("assistant", message)
