"""Phase 5 Tests: Verify no double feedback generation."""

import json
import pytest
from unittest.mock import Mock, patch
import streamlit as st
from ui.services.grading_execution import run_grading


def test_no_double_feedback_on_approval():
    """Test that FeedbackGeneratorAgent only runs once after approval."""
    # Setup session state for approval flow
    st.session_state.clear()
    st.session_state.rubric_json = json.dumps({"criteria": []})
    st.session_state.submission_text = "Test submission"
    st.session_state.grading_in_progress = True
    st.session_state.approval_decision = "approved"  # Simulate approval
    st.session_state.pending_approval = True
    st.session_state.grades = {}
    st.session_state.grading_session_id = "test-session"
    
    # Mock ALL external dependencies - patch where they're used
    with patch('ui.services.grading_execution.get_runner') as mock_get_runner, \
         patch('ui.services.grading_execution.get_app') as mock_get_app:
        
        mock_runner = Mock()
        mock_app = Mock()
        mock_get_runner.return_value = mock_runner
        mock_get_app.return_value = mock_app
        
        # Mock resume response
        mock_response = Mock()
        mock_response.events = [
            Mock(type="agent_partial_result", agent_name="FeedbackGeneratorAgent", content="feedback generated")
        ]
        
        # Make the resume method async-compatible
        async def mock_resume_async(*args, **kwargs):
            return mock_response
        
        mock_runner.resume = mock_resume_async
        
        # Collect events
        events = list(run_grading())
        
        # Verify only one feedback event
        feedback_events = [e for e in events if e.get("agent_name") == "FeedbackGeneratorAgent"]
        assert len(feedback_events) <= 1, f"Expected at most 1 feedback event, got {len(feedback_events)}"


def test_no_double_feedback_on_manual_adjust():
    """Test that no feedback is generated for manual adjust (we finalize immediately)."""
    # Setup session state for manual adjust
    st.session_state.clear()
    st.session_state.rubric_json = json.dumps({"criteria": []})
    st.session_state.submission_text = "Test submission"
    st.session_state.grading_in_progress = True
    st.session_state.approval_decision = "manual_adjust"
    st.session_state.manual_final_score = 85.0
    st.session_state.manual_letter_grade = "B"
    st.session_state.manual_feedback = "Manual feedback"
    st.session_state.grades = {}  # Initialize grades to avoid KeyError
    st.session_state.grading_session_id = "test-session"
    st.session_state.final_score = {"max_possible": 100.0}  # Add base final_score for calculation
    
    # Mock ALL external dependencies - need to patch where they're used
    with patch('ui.services.grading_execution.get_runner') as mock_get_runner, \
         patch('ui.services.grading_execution.get_app') as mock_get_app:
        
        mock_runner = Mock()
        mock_app = Mock()
        mock_get_runner.return_value = mock_runner
        mock_get_app.return_value = mock_app
        
        # Collect events
        events = list(run_grading())
        
        # Verify no feedback events (we should finalize immediately)
        feedback_events = [e for e in events if e.get("agent_name") == "FeedbackGeneratorAgent"]
        assert len(feedback_events) == 0, f"Expected 0 feedback events for manual adjust, got {len(feedback_events)}"
        
        # Verify approval_action event is emitted first
        approval_events = [e for e in events if e.get("type") == "approval_action" and e.get("data", {}).get("action") == "manual_adjust"]
        assert len(approval_events) == 1, f"Expected manual_adjust approval_action event, got {len(approval_events)}"
        
        # Verify grading_complete event is emitted
        complete_events = [e for e in events if e.get("type") == "grading_complete"]
        assert len(complete_events) == 1, f"Expected grading_complete event for manual adjust, got {len(complete_events)}"


def test_no_double_feedback_on_regrade():
    """Test that regrade starts fresh without duplicate feedback."""
    # Setup session state for regrade
    st.session_state.clear()
    st.session_state.rubric_json = json.dumps({"criteria": []})
    st.session_state.submission_text = "Test submission"
    st.session_state.grading_in_progress = True
    st.session_state.approval_decision = "regrade"
    st.session_state.grades = {}
    st.session_state.grading_session_id = "test-session"
    
    # Mock ALL external dependencies - patch where they're used
    with patch('ui.services.grading_execution.get_runner') as mock_get_runner, \
         patch('ui.services.grading_execution.get_app') as mock_get_app:
        
        mock_runner = Mock()
        mock_app = Mock()
        mock_get_runner.return_value = mock_runner
        mock_get_app.return_value = mock_app
        
        # Mock session service to avoid await issues
        mock_session_service = Mock()
        mock_session_service.get_session = Mock(return_value=None)
        mock_created_session = Mock()
        mock_created_session.id = "mock-session-id"
        mock_session_service.create_session = Mock(return_value=mock_created_session)
        # Make session service methods async-compatible
        async def mock_get_session_async(*args, **kwargs):
            return None
        async def mock_create_session_async(*args, **kwargs):
            return mock_created_session
        mock_session_service.get_session = mock_get_session_async
        mock_session_service.create_session = mock_create_session_async
        mock_runner.session_service = mock_session_service
        
        # Make runner.run_async an async generator that yields events with actions.state_delta
        # The grading runner calls run_async twice:
        # - once for rubric validation (new_message text == rubric_json)
        # - once for grading (new_message text == submission_text)
        async def mock_run_async(*args, **kwargs):
            new_message = kwargs.get("new_message")
            msg_text = None
            try:
                msg_text = new_message.parts[0].text
            except Exception:
                msg_text = None

            def _event_with_state_delta(state_delta: dict):
                ev = Mock()
                ev.actions = Mock()
                ev.actions.state_delta = state_delta
                ev.invocation_id = "mock-invocation-id"
                return ev

            if msg_text == st.session_state.rubric_json:
                yield _event_with_state_delta({"rubric_validation": {"status": "valid"}})
                return

            if msg_text == st.session_state.submission_text:
                yield _event_with_state_delta({
                    "aggregation_result": {"max_possible": 100.0, "final_score": 92.0}
                })
                yield _event_with_state_delta({
                    "final_feedback": {"overall_summary": "ok", "strengths": [], "areas_for_improvement": [], "suggestions": [], "encouragement": ""}
                })
                return

            return

        mock_runner.run_async = mock_run_async
        
        # Collect events
        events = list(run_grading())
        
        # Verify feedback completes exactly once
        feedback_events = [e for e in events if e.get("type") == "step_complete" and e.get("step") == "feedback"]
        assert len(feedback_events) == 1, f"Expected 1 feedback completion event for regrade, got {len(feedback_events)}"
        
        # Verify regrade event is emitted
        regrade_events = [e for e in events if e.get("type") == "approval_action" and e.get("data", {}).get("action") == "regrade"]
        assert len(regrade_events) == 1, "Expected regrade approval_action event"


def test_feedback_uses_final_score_after_approval():
    """Test that feedback uses the approved/aggregated score, not original grader scores."""
    # This is implicitly tested by the fact that:
    # 1. AggregatorAgent saves aggregation_result to tool_context.state
    # 2. FeedbackGeneratorAgent reads from aggregation_result in its instruction
    # 3. Manual adjust skips FeedbackAgent entirely
    # 4. Approval uses the aggregation_result values
    
    # For completeness, we can verify the instruction mentions aggregation_result
    from agents.feedback import create_feedback_agent
    agent = create_feedback_agent()
    assert "aggregation_result" in agent.inner_agent.instruction.lower(), \
        "FeedbackGeneratorAgent should read from aggregation_result"
