import streamlit as st
from typing import Callable, Optional

def render_approval_tab(on_approve: Optional[Callable] = None, on_reject: Optional[Callable] = None):
    """Render the approval interface in a tab."""
    st.header("🛡️ Human Approval Required")
    
    if not st.session_state.get("pending_approval", False):
        st.info("No pending approvals at this moment. The grading process runs automatically unless an intervention is required.")
        return

    reason = st.session_state.get("approval_reason", "Verification required")
    st.warning(f"Reason: {reason}")
    
    # Display context/details if available
    confirmations = st.session_state.get("requested_tool_confirmations")
    if confirmations:
        st.subheader("Requested Confirmations")
        for tool_name, details in confirmations.items():
            with st.expander(f"Tool: {tool_name}", expanded=True):
                st.json(details)

    action = st.radio(
        "Decision",
        options=["Approve", "Manual Adjust", "Regrade"],
        index=0,
        horizontal=True,
    )

    manual_score = None
    manual_letter = None
    manual_feedback = None
    if action == "Manual Adjust":
        st.subheader("Manual Adjust")
        manual_score = st.number_input(
            "Final score",
            value=float(st.session_state.get("manual_final_score", 0.0)),
            step=0.5,
        )
        manual_letter = st.text_input(
            "Letter grade",
            value=str(st.session_state.get("manual_letter_grade", "")),
        )
        manual_feedback = st.text_area(
            "Manual feedback",
            value=str(st.session_state.get("manual_feedback", "")),
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        primary_label = {
            "Approve": "✅ Approve / Continue",
            "Manual Adjust": "✏️ Manual Adjust & Finalize",
            "Regrade": "🔄 Regrade From Start",
        }.get(action, "✅ Confirm")

        if st.button(primary_label, type="primary", width="stretch"):
            if action == "Approve":
                st.session_state.approval_decision = "approved"
            elif action == "Manual Adjust":
                st.session_state.approval_decision = "manual_adjust"
                st.session_state.manual_final_score = float(manual_score) if manual_score is not None else None
                st.session_state.manual_letter_grade = manual_letter
                st.session_state.manual_feedback = manual_feedback
            else:
                st.session_state.approval_decision = "regrade"

            st.session_state.pending_approval = False
            st.session_state.grading_in_progress = True

            if on_approve:
                on_approve()

            st.rerun()
            
    with col2:
        if st.button("↩️ Cancel & Finalize", type="secondary", width='stretch'):
            st.session_state.approval_decision = "cancelled"
            st.session_state.pending_approval = False
            st.session_state.grading_in_progress = True
            
            if on_reject:
                on_reject()
                
            st.rerun()
