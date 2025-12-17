import asyncio
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

# Ensure repo and capstone roots are on sys.path for `ui.*` imports
REPO_ROOT = Path(__file__).resolve().parents[2]
CAPSTONE_ROOT = REPO_ROOT
for p in (str(REPO_ROOT), str(CAPSTONE_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


class MockSessionState(dict):
    """Lightweight stand-in for st.session_state."""

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


def setup_state(st_module):
    """Initialize minimal session_state keys for grading service tests."""
    st_module.session_state = MockSessionState(
        grading_session_id="session-123",
        rubric_json=None,
        submission_text=None,
        grades={},
        final_score=None,
        feedback=None,
        pending_approval=False,
        approval_reason=None,
    )


def test_simulated_grading_flow(monkeypatch):
    """
    Validate simulation fallback emits expected event sequence and populates state.
    """
    # Ensure repo root on path for `ui` imports
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import streamlit as st
    setup_state(st)

    # Load grading service after session_state patch
    from ui.services import grading

    rubric = {
        "name": "Test Rubric",
        "criteria": [
            {"name": "Quality", "max_score": 50, "description": "Code quality"},
            {"name": "Docs", "max_score": 50, "description": "Documentation"},
        ],
    }
    st.session_state.rubric_json = json.dumps(rubric)
    st.session_state.submission_text = "print('hello')"

    events = list(grading.run_grading())
    steps = [e["step"] for e in events if "step" in e]

    assert steps[0] == "validating"
    assert "grading" in steps
    assert "aggregating" in steps
    assert "feedback" in steps
    assert any(e["type"] == "criterion_graded" for e in events)
    assert any(e["type"] == "grading_complete" for e in events)

    # State populated
    assert st.session_state.grades
    assert st.session_state.final_score is not None
    assert st.session_state.feedback is not None


def test_runner_event_mapping_generic(monkeypatch):
    """
    Ensure _map_runner_event returns a safe structure for unknown dict events.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from ui.services import grading

    raw = {"foo": "bar"}
    mapped = grading._map_runner_event(raw)
    assert mapped["type"] == "event"
    assert mapped["step"] == "runner"


def test_runner_event_mapping_structured(monkeypatch):
    """
    Ensure structured runner events pass through.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from ui.services import grading

    raw = {"type": "step_start", "step": "validating", "data": {"message": "ok"}}
    mapped = grading._map_runner_event(raw)
    assert mapped == raw


def test_runner_wrapper_consumes_async(monkeypatch):
    """
    Smoke test _run_runner_events mapping loop using a fake runner.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import streamlit as st
    setup_state(st)

    calls = {"rubric": 0, "submission": 0}

    class FakeRunner:
        async def run_async(self, user_id: str, session_id: str, new_message: Any):
            payload = json.loads(new_message)
            if "rubric" in payload:
                calls["rubric"] += 1
                yield {"type": "step_start", "step": "validating", "data": {"message": "validating..."}}
                yield {"type": "step_complete", "step": "validating", "data": {"message": "ok"}}
            if "submission" in payload:
                calls["submission"] += 1
                yield {"type": "step_start", "step": "grading", "data": {"message": "grading..."}}
                yield {"type": "grading_complete", "step": "complete", "data": {"message": "done"}}

    fake_runner = FakeRunner()

    # Patch grading module runner and session_service
    async def fake_get_session(**kwargs):
        return types.SimpleNamespace(id="s1")

    monkeypatch.setattr(
        "ui.services.grading.runner",
        types.SimpleNamespace(run_async=fake_runner.run_async, session_service=types.SimpleNamespace(get_session=fake_get_session)),
    )
    monkeypatch.setattr("ui.services.grading.grading_app", types.SimpleNamespace(name="app"))
    monkeypatch.setattr("ui.services.grading.ADK_AVAILABLE", True)

    from ui.services import grading

    st.session_state.rubric_json = json.dumps({"criteria": [{"name": "Q", "max_score": 1, "description": "d"}]})
    st.session_state.submission_text = "print('x')"

    async def collect():
        evs = []
        async for ev in grading._run_runner_events(st.session_state.rubric_json, st.session_state.submission_text):
            evs.append(ev)
        return evs

    events = asyncio.run(collect())

    # Should have consumed both rubric and submission
    assert calls["rubric"] == 1
    assert calls["submission"] == 1
    assert any(ev["data"].get("step") == "validating" for ev in events if "data" in ev)
    assert any(ev["data"].get("step") == "complete" or ev.get("type") == "grading_complete" for ev in events)
