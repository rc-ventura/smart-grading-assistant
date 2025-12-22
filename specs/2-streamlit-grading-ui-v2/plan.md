# Implementation Plan: Smart Grading Streamlit UI v2 (UX Overhaul)

**Branch**: `2-streamlit-grading-ui-v2` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/2-streamlit-grading-ui-v2/spec.md`

---

## Summary

Improve the Streamlit grading UI into a chat-first, non-blocking experience with tabs (Chat/Results/Debug), incremental progress updates, and robust session lifecycle so the teacher can grade multiple submissions without restarting Streamlit.

---

## Technical Context

- **Language/Version**: Python (same repo baseline)
- **Frontend**: Streamlit
- **Backend**: ADK Runner already integrated via `capstone/ui/services/grading.py`
- **State**:
  - Backend remains canonical for grading outputs
  - UI uses `st.session_state` for display/runtime state
- **Testing**:
  - pytest for service/event mapping
  - optional `streamlit.testing.AppTest` for automated E2E smoke

---

## Architecture & Key Decisions

### Chat-first + Tabs

- Move primary user experience into **Chat** tab.
- Move detailed output to **Results** tab.
- Provide troubleshooting visibility in **Debug** tab (off by default; optional toggles).

### Event Streaming UX

- Ensure immediate visual feedback after start (progress shell).
- Append/merge Runner events into an event buffer in session state.
- Render chat updates incrementally using stable placeholders/containers.

### Session Lifecycle

- Define a safe reset path (new run) that clears transient state.
- On backend/session errors (“backend closed”), recreate session and continue.

---

## Milestones

### Milestone 1: UX skeleton (tabs + basic containers) ✅
- [x] Add tabs and move existing content into them without changing core behavior.
- [x] Create stable placeholders in Chat tab for progress + event feed.

### Milestone 2: Incremental updates + progress clarity ✅
- [x] Reduce chat noise/duplication.
- [x] Show per-criterion updates as they arrive.
- [x] Ensure UI never appears frozen.

### Milestone 3: Approval Flow (Human-in-the-Loop) ✅
- [x] Implement approval modal/flow (<50% or >90%) with confirm/adjust grade.
- [x] Integrate with session persistence for reliable resume.

### Milestone 4: Stability for repeated runs (Current Focus)
- [ ] Fix regrade without restart (session recreation, state reset discipline).
- [ ] Add cancel flow (partial/needs refinement).

### Milestone 5: Debug + tests
- [ ] Debug tab event log + export.
- [ ] Automated E2E smoke test.

### Milestone 6: Configuration Features (Phase F)
- [ ] Add LLM Provider toggle in Sidebar (OpenAI vs Gemini).
- [ ] Refactor `agent.py` to support dynamic app/runner initialization based on selected provider.
- [ ] Update `ui/services/grading.py` to invalidate/recreate runner when provider changes.

---

## Risks & Mitigations

- **Streamlit reruns causing duplicated rendering**: use stable placeholders and event IDs/de-dup.
- **Runner lifecycle / closed backend**: catch exceptions, recreate session, re-run with clear UI messaging.
- **Long runs**: cancel flow + ongoing progress.

---

## Next Steps

1. Implement Milestone 1 (tabs + layout refactor)
2. Implement incremental streaming UX
3. Fix regrade without restart
4. Add debug tab + automated E2E smoke
