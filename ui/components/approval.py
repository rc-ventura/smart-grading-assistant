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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve / Continue", type="primary", use_container_width=True):
            st.session_state.approval_decision = "approved"
            st.session_state.pending_approval = False
            # Clear reason and confirmations to reset UI state
            st.session_state.approval_reason = None
            st.session_state.requested_tool_confirmations = None
            st.session_state.grading_in_progress = True
            
            if on_approve:
                on_approve()
            
            st.rerun()
            
    with col2:
        if st.button("❌ Reject / Stop", type="secondary", use_container_width=True):
            st.session_state.approval_decision = "rejected"
            st.session_state.pending_approval = False
            st.session_state.approval_reason = None
            st.session_state.requested_tool_confirmations = None
            st.session_state.grading_in_progress = False # Stop grading on reject? Or resume with rejection?
            # Usually rejection means "don't do the action" or "stop". 
            # If it's a tool confirmation, rejection might mean "don't run tool" but continue workflow?
            # For now, let's assume we want to resume with the rejection decision.
            st.session_state.grading_in_progress = True
            
            if on_reject:
                on_reject()
                
            st.rerun()
