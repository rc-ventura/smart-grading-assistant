import contextlib
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(REPO_ROOT),):
    if p not in sys.path:
        sys.path.insert(0, p)


class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class _Slot:
    @contextlib.contextmanager
    def container(self):
        yield


class _RerunRequested(RuntimeError):
    pass


def _setup_state(st_module):
    st_module.session_state = MockSessionState(
        cancel_requested=False,
        grading_in_progress=True,
        current_step="grading",
        pending_approval=True,
        approval_decision="approve",
        messages=[],
        event_log=[],
        _event_log_index={},
        _seen_step_start={},
        _seen_step_complete={},
        _seen_criteria={},
        _pending_approval_notified=False,
        error_message=None,
        grades={},
        rubric_json='{"name": "Test", "criteria": []}',
        submission_text="test submission",
    )


def test_cancel_immediate_resets_state_and_reruns(monkeypatch):
    import streamlit as st

    _setup_state(st)
    st.session_state.cancel_requested = True

    from ui.services import grading_consumer

    monkeypatch.setattr(
        "ui.services.grading.run_grading",
        lambda: iter(()),
        raising=True,
    )

    msgs = []

    def fake_add_message(role, text):
        msgs.append((role, text))

    monkeypatch.setattr(
        "ui.services.grading_consumer.add_message",
        fake_add_message,
        raising=True,
    )
    monkeypatch.setattr(
        "ui.services.grading_consumer.render_chat",
        lambda: None,
        raising=True,
    )

    monkeypatch.setattr(st, "rerun", lambda: (_ for _ in ()).throw(_RerunRequested()))

    with pytest.raises(_RerunRequested):
        grading_consumer.consume_grading_events(_Slot(), _Slot())

    assert st.session_state.cancel_requested is False
    assert st.session_state.grading_in_progress is False
    assert st.session_state.current_step == "idle"
    assert st.session_state.pending_approval is False
    assert st.session_state.approval_decision is None
    assert any("cancelled" in t.lower() for _, t in msgs)


def test_cancel_mid_stream_breaks_and_resets(monkeypatch):
    import streamlit as st

    _setup_state(st)

    from ui.services import grading_consumer

    def fake_run_grading():
        yield {"type": "step_start", "step": "grading", "data": {"message": "x"}}
        st.session_state.cancel_requested = True
        yield {"type": "criterion_graded", "step": "grading", "data": {"criterion_name": "C"}}

    monkeypatch.setattr(
        "ui.services.grading_consumer.run_grading",
        fake_run_grading,
        raising=True,
    )

    msgs = []

    def fake_add_message(role, text):
        msgs.append((role, text))

    monkeypatch.setattr(
        "ui.services.grading_consumer.add_message",
        fake_add_message,
        raising=True,
    )
    monkeypatch.setattr(
        "ui.services.grading_consumer.render_chat",
        lambda: None,
        raising=True,
    )

    monkeypatch.setattr(st, "rerun", lambda: None)

    grading_consumer.consume_grading_events(_Slot(), _Slot())

    assert st.session_state.cancel_requested is False
    assert st.session_state.grading_in_progress is False
    assert st.session_state.current_step == "idle"
    assert st.session_state.pending_approval is False
    assert st.session_state.approval_decision is None
    assert any("cancelled" in t.lower() for _, t in msgs)
