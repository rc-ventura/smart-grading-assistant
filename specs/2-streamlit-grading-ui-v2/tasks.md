# Tasks: Smart Grading Streamlit UI v2 (UX Overhaul)

**Input**: Design documents from `/specs/2-streamlit-grading-ui-v2/`
**Prerequisites**: spec.md ✅, plan.md ✅

**Purpose**: Improve UI/UX (chat-first, tabs, incremental progress, debug visibility) and fix stability issues for repeated runs.

---

## Phase A: Layout Refactor (Tabs + separation of concerns)

- [ ] UIV2-001 Create tabs in `capstone/ui/app.py`: Chat / Results / Debug
- [ ] UIV2-002 Move existing chat rendering into Chat tab
- [ ] UIV2-003 Move existing results rendering into Results tab
- [ ] UIV2-004 Add Debug tab placeholder (empty state)

**Checkpoint**: App renders with tabs and existing functionality preserved.

---

## Phase B: Streaming UX (Incremental, non-blocking)

- [ ] UIV2-010 Replace abrupt placeholders with stable containers in Chat tab (progress shell)
- [ ] UIV2-011 Add event buffer in `st.session_state` (ordered log + dedup)
- [ ] UIV2-012 Improve event → chat mapping (reduce duplication/noise)
- [ ] UIV2-013 Show per-criterion updates with consistent formatting as they arrive

**Checkpoint**: During grading, UI updates incrementally and never appears frozen.

---

## Phase C: Stability (regrade + cancel + recovery)

- [ ] UIV2-020 Fix regrade flow without restarting Streamlit (reset transient state, recreate session on "backend closed")
- [ ] UIV2-021 Add "Cancel grading" action that stops event consumption safely
- [ ] UIV2-022 Ensure errors are recoverable (clear messaging + safe reset)

**Checkpoint**: Multiple runs work reliably without restarting Streamlit.

---

## Phase D: Approval Flow (migrated from Integration Sprint)

- [ ] UIV2-030 Implement approval modal/flow (<50% or >90%) with confirm/adjust grade

---

## Phase E: Cleanup + Tests (migrated + new)

- [ ] UIV2-040 Delete legacy code (final cleanup) (was T1007)
- [ ] UIV2-041 Unit tests for H001/I002 mapping robustness (parse/repair JSON, per-criterion retries) (was TTEST01)
- [ ] UIV2-042 Automated E2E smoke test for Streamlit UI (prefer `streamlit.testing.AppTest`) (was TTEST02)

---

## Debug Tab Enhancements

- [ ] UIV2-050 Debug tab: toggle to show raw Runner events/state deltas
- [ ] UIV2-051 Debug tab: export/download event log
