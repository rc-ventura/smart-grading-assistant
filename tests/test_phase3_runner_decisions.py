import sys
from pathlib import Path

import pytest


# Ensure repo root on sys.path for `ui.*` imports
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


def _base_state(st_module):
    st_module.session_state = MockSessionState(
        grading_session_id="session-123",
        rubric_json="{}",
        submission_text="submission",
        rubric_valid=True,
        rubric_errors=[],
        grades={"C1": {"criterion_name": "C1", "score": 1, "max_score": 2}},
        final_score={"max_possible": 10, "total_score": 1, "percentage": 10.0, "letter_grade": "F"},
        feedback={"overall_summary": "old"},
        pending_approval=True,
        approval_reason="edge",
        requested_tool_confirmations={"call1": {"hint": "confirm"}},
        last_invocation_id="inv1",
        approval_decision=None,
        approval_followup={"stage": "choose_action"},
        regrade_comment="please regrade",
        manual_final_score=None,
        manual_letter_grade=None,
        manual_feedback=None,
        grading_in_progress=True,
        current_step="approval",
    )


def test_run_grading_manual_adjust_finalizes_immediately(monkeypatch):
    import streamlit as st
    from ui.services import grading_execution

    _base_state(st)

    st.session_state.approval_decision = "manual_adjust"
    st.session_state.manual_final_score = 7
    st.session_state.manual_letter_grade = "B"
    st.session_state.manual_feedback = "Manual feedback text"

    # runner/app must be present, but should not be used for manual_adjust
    monkeypatch.setattr(grading_execution, "get_runner", lambda: object())
    monkeypatch.setattr(grading_execution, "get_app", lambda: object())

    events = list(grading_execution.run_grading())

    assert len(events) == 2
    assert events[0]["type"] == "approval_action"
    assert events[0]["step"] == "approval"
    assert events[0]["data"]["action"] == "manual_adjust"
    assert events[1]["type"] == "grading_complete"
    assert st.session_state.current_step == "complete"
    assert st.session_state.pending_approval is False
    assert st.session_state.approval_decision is None
    assert st.session_state.approval_followup is None
    assert st.session_state.regrade_comment == ""
    assert st.session_state.final_score["total_score"] == 7.0
    assert st.session_state.final_score["letter_grade"] == "B"
    assert st.session_state.feedback["overall_summary"] == "Manual feedback text"


def test_run_grading_regrade_resets_state_and_restarts(monkeypatch):
    import streamlit as st
    from ui.services import grading_execution

    _base_state(st)

    st.session_state.approval_decision = "regrade"

    called = {"run": 0}

    async def fake_run_runner_events_impl(*args, **kwargs):
        called["run"] += 1
        if False:
            yield  # pragma: no cover

    monkeypatch.setattr(grading_execution, "get_runner", lambda: object())
    monkeypatch.setattr(grading_execution, "get_app", lambda: object())
    monkeypatch.setattr(grading_execution, "run_runner_events_impl", fake_run_runner_events_impl)

    events = list(grading_execution.run_grading())

    assert events[0]["type"] == "approval_action"
    assert events[0]["step"] == "approval"
    assert events[0]["data"]["action"] == "regrade"
    assert any(ev.get("type") == "step_start" and ev.get("step") == "regrade" for ev in events)

    assert called["run"] == 1
    assert st.session_state.grades == {}
    assert st.session_state.final_score is None
    assert st.session_state.feedback is None
    assert st.session_state.grading_session_id is None
    assert st.session_state.approval_followup is None
    assert st.session_state.regrade_comment == ""
