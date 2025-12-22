"""Integration tests for LLM provider switching and state management."""

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st


class MockSessionState(dict):
    """Mock for st.session_state."""
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value


@pytest.fixture
def mock_st():
    """Mock streamlit module."""
    mock = MagicMock()
    mock.session_state = MockSessionState()
    return mock


def test_provider_switch_invalidates_runner(mock_st, monkeypatch):
    """Test that switching provider invalidates cached runner."""
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from ui.services import grading_lifecycle
    
    # Mock ADK components
    monkeypatch.setattr(grading_lifecycle, "ADK_AVAILABLE", True)
    monkeypatch.setattr(grading_lifecycle, "create_grading_runner", 
                       lambda provider: (MagicMock(name=f"runner_{provider}"), 
                                       MagicMock(name=f"app_{provider}")))
    
    # First call with gemini
    mock_st.session_state["llm_provider"] = "gemini"
    runner1 = grading_lifecycle.get_runner()
    app1 = grading_lifecycle.get_app()
    
    assert runner1 is not None
    assert app1 is not None
    assert mock_st.session_state.get("_adk_provider") == "gemini"
    
    # Switch to openai - should invalidate and recreate
    mock_st.session_state["llm_provider"] = "openai"
    runner2 = grading_lifecycle.get_runner()
    app2 = grading_lifecycle.get_app()
    
    assert runner2 is not None
    assert app2 is not None
    assert mock_st.session_state.get("_adk_provider") == "openai"
    
    # Runners should be different instances
    assert runner1.name != runner2.name
    assert app1.name != app2.name


def test_provider_switch_clears_approval_state(mock_st, monkeypatch):
    """Test that invalidate_runner clears approval/resume state."""
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from ui.services import grading_lifecycle
    
    # Set up approval state
    mock_st.session_state["last_invocation_id"] = "inv-123"
    mock_st.session_state["approval_decision"] = "approve"
    mock_st.session_state["pending_approval"] = True
    mock_st.session_state["requested_tool_confirmations"] = {"call1": {}}
    mock_st.session_state["_adk_runner"] = MagicMock()
    mock_st.session_state["_adk_app"] = MagicMock()
    mock_st.session_state["_adk_provider"] = "gemini"
    
    # Invalidate runner
    grading_lifecycle.invalidate_runner()
    
    # Approval state should be cleared
    assert mock_st.session_state.get("last_invocation_id") is None
    assert mock_st.session_state.get("approval_decision") is None
    assert mock_st.session_state.get("pending_approval") is False
    assert mock_st.session_state.get("requested_tool_confirmations") is None
    
    # Runner/app should be cleared
    assert "_adk_runner" not in mock_st.session_state
    assert "_adk_app" not in mock_st.session_state
    assert "_adk_provider" not in mock_st.session_state


def test_same_provider_reuses_cached_runner(mock_st, monkeypatch):
    """Test that same provider reuses cached runner without recreation."""
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from ui.services import grading_lifecycle
    
    # Mock ADK components
    monkeypatch.setattr(grading_lifecycle, "ADK_AVAILABLE", True)
    
    call_count = {"count": 0}
    def mock_create_runner(provider):
        call_count["count"] += 1
        return (MagicMock(name=f"runner_{provider}_{call_count['count']}"), 
                MagicMock(name=f"app_{provider}_{call_count['count']}"))
    
    monkeypatch.setattr(grading_lifecycle, "create_grading_runner", mock_create_runner)
    
    # First call
    mock_st.session_state["llm_provider"] = "gemini"
    runner1 = grading_lifecycle.get_runner()
    assert call_count["count"] == 1
    
    # Second call with same provider - should reuse cache
    runner2 = grading_lifecycle.get_runner()
    assert call_count["count"] == 1  # No new creation
    assert runner1 is runner2  # Same instance


def test_adk_unavailable_returns_none(mock_st, monkeypatch):
    """Test that get_runner returns None when ADK is unavailable."""
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from ui.services import grading_lifecycle
    
    # Mock ADK as unavailable
    monkeypatch.setattr(grading_lifecycle, "ADK_AVAILABLE", False)
    
    runner = grading_lifecycle.get_runner()
    app = grading_lifecycle.get_app()
    
    assert runner is None
    assert app is None


def test_factory_creates_fresh_agents_per_provider():
    """Test that create_grading_runner creates fresh agent instances."""
    from agent import create_grading_runner
    
    # Create runners for different providers
    runner1, app1 = create_grading_runner(provider="gemini")
    runner2, app2 = create_grading_runner(provider="openai")
    
    # Should be different instances
    assert runner1 is not runner2
    assert app1 is not app2
    
    # Both should be valid
    assert runner1 is not None
    assert runner2 is not None
    assert app1 is not None
    assert app2 is not None
    
    # Apps should have same structure but different agent instances
    assert app1.name == app2.name  # Same app name
    assert app1.root_agent is not app2.root_agent  # Different agent instances
