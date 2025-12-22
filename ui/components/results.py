"""Results and feedback display component."""

import json
from typing import Any

import streamlit as st

from ui.utils.formatters import (
    format_score,
    format_letter_grade,
    format_feedback,
    format_percentage,
)


def render_results() -> None:
    """Render the results panel with scores and feedback."""
    
    # Only show results when grading is complete
    if st.session_state.current_step != "complete":
        st.info("Grading is not complete yet")
        st.container()
        return
    
    st.header("📊 Grading Results")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Final Score Card
    # ─────────────────────────────────────────────────────────────────────────
    _render_final_score()
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Per-Criterion Scores Table
    # ─────────────────────────────────────────────────────────────────────────
    _render_criterion_table()
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Feedback Panel
    # ─────────────────────────────────────────────────────────────────────────
    _render_feedback_panel()


def render_reports() -> None:
    if st.session_state.current_step != "complete":
        st.info("Reports are not available yet")
        st.container()
        return

    st.header("📤 Reports")

    # ─────────────────────────────────────────────────────────────────────────
    # Export Options
    # ─────────────────────────────────────────────────────────────────────────
    _render_export_options()


def _render_final_score() -> None:
    """Render the final score card."""
    final_score = st.session_state.final_score
    
    if not final_score:
        st.warning("Final score not available")
        return
    
    total = final_score.get("total_score", 0)
    max_possible = final_score.get("max_possible", 0)
    percentage = final_score.get("percentage", 0)
    letter = final_score.get("letter_grade", "N/A")
    
    # Color based on grade
    if percentage >= 90:
        grade_color = "🟢"
        grade_emoji = "🎉"
    elif percentage >= 80:
        grade_color = "🟢"
        grade_emoji = "👍"
    elif percentage >= 70:
        grade_color = "🟡"
        grade_emoji = "📝"
    elif percentage >= 60:
        grade_color = "🟠"
        grade_emoji = "⚠️"
    else:
        grade_color = "🔴"
        grade_emoji = "📚"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Score",
            value=f"{total:.1f} / {max_possible:.0f}",
        )
    
    with col2:
        st.metric(
            label="Percentage",
            value=f"{percentage:.1f}%",
        )
    
    with col3:
        st.metric(
            label=f"{grade_color} Letter Grade",
            value=f"{grade_emoji} {letter}",
        )
    
    # Approval notice
    if final_score.get("requires_human_approval") or final_score.get("requires_approval"):
        reason = final_score.get("approval_reason", "Edge case detected")
        st.warning(f"⚠️ **Approval Required:** {reason}")


def _render_criterion_table() -> None:
    """Render the per-criterion scores table."""
    grades = st.session_state.grades
    final_score = st.session_state.final_score
    grade_details = None
    if isinstance(final_score, dict):
        gd = final_score.get("grade_details")
        if isinstance(gd, list):
            grade_details = gd
    
    if not grades and not grade_details:
        st.info("No criterion grades available")
        return
    
    st.subheader("📋 Per-Criterion Breakdown")
    
    # Build table data
    table_data = []

    if grade_details:
        for detail in grade_details or []:
            if not isinstance(detail, dict):
                continue
            criterion_name = detail.get("criterion", "Unknown")
            score = detail.get("score", 0)
            max_score = detail.get("max_score", 0)
            notes = detail.get("evaluation_notes") or detail.get("justification") or "No notes"
            percentage = (score / max_score * 100) if max_score > 0 else 0

            table_data.append({
                "Criterion": criterion_name,
                "Score": f"{score:.1f} / {max_score:.0f}",
                "Percentage": f"{percentage:.0f}%",
                "Notes": notes[:100] + "..." if len(notes) > 100 else notes,
            })
    else:
        for criterion_name, grade_data in grades.items():
            score = grade_data.get("score", 0)
            max_score = grade_data.get("max_score", 0)
            notes = grade_data.get("evaluation_notes") or grade_data.get("justification") or "No notes"
            percentage = (score / max_score * 100) if max_score > 0 else 0

            table_data.append({
                "Criterion": criterion_name,
                "Score": f"{score:.1f} / {max_score:.0f}",
                "Percentage": f"{percentage:.0f}%",
                "Notes": notes[:100] + "..." if len(notes) > 100 else notes,
            })
    
    # Display as dataframe
    st.dataframe(
        table_data,
        width="stretch",
        hide_index=True,
    )
    
    # Expandable details for each criterion
    with st.expander("📝 Detailed Evaluation Notes", expanded=False):
        if grade_details:
            for detail in grade_details or []:
                if not isinstance(detail, dict):
                    continue
                criterion_name = detail.get("criterion", "Unknown")
                st.markdown(f"**{criterion_name}**")
                notes = detail.get("evaluation_notes") or detail.get("justification") or "No notes available"
                st.write(notes)
                st.divider()
        else:
            for criterion_name, grade_data in grades.items():
                st.markdown(f"**{criterion_name}**")
                notes = grade_data.get("evaluation_notes") or grade_data.get("justification") or "No notes available"
                st.write(notes)
                st.divider()


def _render_feedback_panel() -> None:
    """Render the feedback expander with strengths, improvements, suggestions."""
    feedback = st.session_state.feedback
    
    st.subheader("💬 Feedback")
    
    with st.expander("View Detailed Feedback", expanded=True):
        if not feedback:
            st.info("No feedback generated yet")
            return
        
        if isinstance(feedback, dict):
            # Structured feedback
            if strengths := feedback.get("strengths"):
                st.markdown("### ✅ Strengths")
                if isinstance(strengths, list):
                    for item in strengths:
                        st.markdown(f"- {item}")
                else:
                    st.write(strengths)
            
            if improvements := feedback.get("improvements"):
                st.markdown("### 📈 Areas for Improvement")
                if isinstance(improvements, list):
                    for item in improvements:
                        st.markdown(f"- {item}")
                else:
                    st.write(improvements)
            
            if suggestions := feedback.get("suggestions"):
                st.markdown("### 💡 Suggestions")
                if isinstance(suggestions, list):
                    for item in suggestions:
                        st.markdown(f"- {item}")
                else:
                    st.write(suggestions)
            
            if summary := feedback.get("overall_summary"):
                st.markdown("### 📝 Summary")
                st.write(summary)
            
            if encouragement := feedback.get("encouragement"):
                st.info(f"💪 {encouragement}")
        else:
            # Plain text feedback
            st.write(feedback)


def _render_export_options() -> None:
    """Render export buttons for JSON download and clipboard copy."""
    st.subheader("📤 Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as JSON
        export_data = _build_export_data()
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="grading_results.json",
            mime="application/json",
            width="stretch",
            key="download_json_results",
        )
    
    with col2:
        # Copy feedback to clipboard
        feedback_text = _build_feedback_text()
        st.code(feedback_text, language=None)
        st.caption("👆 Click to copy feedback text")


def _build_export_data() -> dict[str, Any]:
    """Build the export data structure."""
    return {
        "session_id": st.session_state.grading_session_id,
        "grades": st.session_state.grades,
        "final_score": st.session_state.final_score,
        "feedback": st.session_state.feedback,
        "rubric_json": st.session_state.rubric_json,
        "submission_preview": (
            st.session_state.submission_text[:500] + "..."
            if st.session_state.submission_text and len(st.session_state.submission_text) > 500
            else st.session_state.submission_text
        ),
    }


def _build_feedback_text() -> str:
    """Build plain text feedback for clipboard."""
    feedback = st.session_state.feedback
    final_score = st.session_state.final_score
    
    lines = ["=== GRADING RESULTS ===\n"]
    
    if final_score:
        lines.append(f"Total Score: {final_score.get('total_score', 0):.1f} / {final_score.get('max_possible', 0):.0f}")
        lines.append(f"Percentage: {final_score.get('percentage', 0):.1f}%")
        lines.append(f"Letter Grade: {final_score.get('letter_grade', 'N/A')}\n")
    
    lines.append("=== FEEDBACK ===\n")
    
    if feedback:
        lines.append(format_feedback(feedback))
    else:
        lines.append("No feedback available.")
    
    return "\n".join(lines)
