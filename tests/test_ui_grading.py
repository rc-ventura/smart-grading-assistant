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
        rubric_valid=False,
        rubric_errors=[],
        grades={},
        final_score=None,
        feedback=None,
        pending_approval=False,
        approval_reason=None,
        error_message=None,
        current_step="idle",
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
    monkeypatch.setattr(grading, "ADK_AVAILABLE", False)

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
    seen_messages: list[Any] = []

    class FakePart:
        def __init__(self, *, text: str):
            self.text = text

    class FakeContent:
        def __init__(self, *, role: str, parts: list[Any]):
            self.role = role
            self.parts = parts

    class FakeRunner:
        async def run_async(self, user_id: str, session_id: str, new_message: Any):
            seen_messages.append(new_message)
            text = None
            parts = getattr(new_message, "parts", None) or []
            if parts:
                text = getattr(parts[0], "text", None)

            if isinstance(text, str) and "criteria" in text:
                calls["rubric"] += 1
                yield {"type": "step_start", "step": "validating", "data": {"message": "validating..."}}
                yield {"type": "step_complete", "step": "validating", "data": {"message": "ok"}}
                return

            if isinstance(text, str):
                calls["submission"] += 1
                yield {"type": "step_start", "step": "grading", "data": {"message": "grading..."}}
                yield {"type": "grading_complete", "step": "complete", "data": {"message": "done"}}

    fake_runner = FakeRunner()

    # Patch grading module runner and session_service
    async def fake_get_session(**kwargs):
        return types.SimpleNamespace(id="s1")

    monkeypatch.setattr(
        "ui.services.grading.runner",
        types.SimpleNamespace(
            run_async=fake_runner.run_async,
            session_service=types.SimpleNamespace(get_session=fake_get_session),
        ),
    )
    monkeypatch.setattr("ui.services.grading.grading_app", types.SimpleNamespace(name="app"))
    monkeypatch.setattr("ui.services.grading.ADK_AVAILABLE", True)
    monkeypatch.setattr(
        "ui.services.grading.types",
        types.SimpleNamespace(Content=FakeContent, Part=FakePart),
    )

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
    assert len(seen_messages) == 2
    assert getattr(seen_messages[0], "role", None) == "user"
    assert getattr(seen_messages[1], "role", None) == "user"
    assert any(
        ev.get("data", {}).get("step") == "validating" or ev.get("data", {}).get("type") == "step_start"
        for ev in events
    )
    assert any(
        ev.get("data", {}).get("step") == "complete"
        or ev.get("data", {}).get("type") == "grading_complete"
        for ev in events
    )


def test_map_runner_event_applies_state_delta_and_tool_confirmations(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import streamlit as st
    setup_state(st)

    from ui.services import grading

    class FakeActions:
        def __init__(self, *, state_delta: dict[str, Any] | None = None, requested_tool_confirmations: dict[str, Any] | None = None):
            self.state_delta = state_delta or {}
            self.requested_tool_confirmations = requested_tool_confirmations or {}

    class FakeEvent:
        def __init__(self, *, actions: FakeActions):
            self.actions = actions
            self.author = "agent"
            self.content = None

    grade_delta = {
        "grade_code_quality": {
            "criterion_name": "Code Quality",
            "score": 8,
            "max_score": 10,
            "evaluation_notes": "ok",
        }
    }
    mapped = grading._map_runner_event(FakeEvent(actions=FakeActions(state_delta=grade_delta)))
    assert mapped["type"] == "criterion_graded"
    assert "Code Quality" in st.session_state.grades

    agg_delta = {
        "aggregation_result": {
            "total_score": 8,
            "max_possible": 10,
            "percentage": 80.0,
            "letter_grade": "B",
            "grade_details": [],
            "requires_human_approval": True,
            "approval_reason": "edge",
        }
    }
    mapped = grading._map_runner_event(FakeEvent(actions=FakeActions(state_delta=agg_delta)))
    assert mapped["type"] == "step_complete"
    assert mapped["step"] == "aggregating"
    assert st.session_state.pending_approval is True
    assert st.session_state.approval_reason == "edge"

    feedback_delta = {
        "final_feedback": {
            "strengths": ["s"],
            "areas_for_improvement": ["i"],
            "suggestions": ["x"],
            "encouragement": "y",
            "overall_summary": "z",
        }
    }
    mapped = grading._map_runner_event(FakeEvent(actions=FakeActions(state_delta=feedback_delta)))
    assert mapped["type"] == "step_complete"
    assert mapped["step"] == "feedback"
    assert st.session_state.feedback is not None
    assert "improvements" in st.session_state.feedback

    mapped = grading._map_runner_event(
        FakeEvent(
            actions=FakeActions(
                requested_tool_confirmations={
                    "call1": {"hint": "approve", "confirmed": False}
                }
            )
        )
    )
    assert mapped["step"] == "approval"
    assert st.session_state.pending_approval is True
    assert st.session_state.approval_reason == "edge"


def test_runner_creates_session_when_missing(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import streamlit as st
    setup_state(st)

    calls = {"get": 0, "create": 0}

    async def fake_get_session(**kwargs):
        calls["get"] += 1
        return None

    async def fake_create_session(**kwargs):
        calls["create"] += 1
        return types.SimpleNamespace(id=kwargs.get("session_id") or "s-new")

    class FakeRunner:
        async def run_async(self, user_id: str, session_id: str, new_message: Any):
            if False:
                yield None

    class FakePart:
        def __init__(self, *, text: str):
            self.text = text

    class FakeContent:
        def __init__(self, *, role: str, parts: list[Any]):
            self.role = role
            self.parts = parts

    monkeypatch.setattr(
        "ui.services.grading.runner",
        types.SimpleNamespace(
            run_async=FakeRunner().run_async,
            session_service=types.SimpleNamespace(
                get_session=fake_get_session,
                create_session=fake_create_session,
            ),
        ),
    )
    monkeypatch.setattr("ui.services.grading.grading_app", types.SimpleNamespace(name="app"))
    monkeypatch.setattr("ui.services.grading.ADK_AVAILABLE", True)
    monkeypatch.setattr(
        "ui.services.grading.types",
        types.SimpleNamespace(Content=FakeContent, Part=FakePart),
    )

    from ui.services import grading

    st.session_state.rubric_json = json.dumps({"criteria": [{"name": "Q", "max_score": 1, "description": "d"}]})
    st.session_state.submission_text = "print('x')"

    async def collect():
        evs = []
        async for ev in grading._run_runner_events(st.session_state.rubric_json, st.session_state.submission_text):
            evs.append(ev)
        return evs

    asyncio.run(collect())
    assert calls["get"] == 1
    assert calls["create"] == 1
