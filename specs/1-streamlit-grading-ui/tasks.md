# Tasks: Smart Grading Streamlit UI

**Input**: Design documents from `/specs/1-streamlit-grading-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested. Test tasks omitted.

**Organization**: Tasks organized by user story to enable independent implementation and testing.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `ui/components/__init__.py` with empty exports
- [X] T002 [P] Create `ui/services/__init__.py` with empty exports
- [X] T003 [P] Create `ui/utils/__init__.py` with empty exports
- [X] T004 Create `ui/utils/formatters.py` with placeholder functions for score/letter formatting

**Checkpoint**: Directory structure ready for component development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user story work

- [X] T005 Refactor `ui/app.py` to initialize all `st.session_state` keys from spec (setup_complete, rubric_json, rubric_valid, submission_text, grading_session_id, grading_in_progress, current_step, grades, final_score, feedback, messages, pending_approval, approval_reason)
- [X] T006 Set up basic layout in `ui/app.py` with sidebar placeholder and main area placeholder
- [X] T007 Add Gemini client initialization at top of `ui/app.py` (GEMINI_API_KEY from st.secrets)

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 — Setup and Start Grading (Priority: P1) 🎯 MVP

**Goal**: Teacher can upload rubric and submission, then start grading

**Independent Test**: Upload a rubric JSON and submission text, verify "Start Grading" button enables

### Implementation for User Story 1

- [X] T008 [US1] Create `ui/components/sidebar.py` with basic structure and imports
- [X] T009 [US1] Implement rubric file upload (`st.file_uploader` for .json) in `ui/components/sidebar.py`
- [X] T010 [US1] Implement rubric text paste (`st.text_area`) in `ui/components/sidebar.py`
- [X] T011 [US1] Add rubric JSON parsing and store in `st.session_state["rubric_json"]`
- [X] T012 [US1] Implement submission file upload (`st.file_uploader` for .py, .txt, .md) in `ui/components/sidebar.py`
- [X] T013 [US1] Implement submission text paste (`st.text_area`) in `ui/components/sidebar.py`
- [X] T014 [US1] Store submission in `st.session_state["submission_text"]`
- [X] T015 [US1] Implement "Start Grading" button (disabled when rubric_valid=false OR submission_text=null) in `ui/components/sidebar.py`
- [X] T016 [US1] Implement "Reset" button that clears session state in `ui/components/sidebar.py`
- [X] T017 [US1] Add session info display (session_id, current_step) in `ui/components/sidebar.py`
- [X] T018 [US1] Wire sidebar component into `ui/app.py` main layout

**Checkpoint**: User Story 1 complete — teacher can upload inputs and trigger grading

---

## Phase 4: User Story 2 — View Grading Progress (Priority: P2)

**Goal**: Teacher sees real-time progress during grading

**Independent Test**: Start grading and verify step indicators update (validating → grading → aggregating → feedback)

### Implementation for User Story 2

- [X] T019 [US2] Create `ui/components/chat.py` with basic structure and imports
- [X] T020 [US2] Implement chat history rendering using `st.chat_message` in `ui/components/chat.py`
- [X] T021 [US2] Implement progress step indicator (current_step display) in `ui/components/chat.py`
- [X] T022 [US2] Implement per-criterion score display as graders complete in `ui/components/chat.py`
- [X] T023 [US2] Add input box for optional teacher queries in `ui/components/chat.py`
- [X] T024 [US2] Update `st.session_state["messages"]` on user input and assistant responses
- [X] T025 [US2] Wire chat component into `ui/app.py` main area

**Checkpoint**: User Story 2 complete — teacher sees grading progress in real-time

---

## Phase 5: User Story 3 — Review Results and Feedback (Priority: P3)

**Goal**: Teacher reviews detailed results and feedback after grading completes

**Independent Test**: Complete grading and verify per-criterion scores, final score, and feedback are displayed

### Implementation for User Story 3

- [X] T026 [US3] Create `ui/components/results.py` with basic structure and imports
- [X] T027 [US3] Implement `format_score()` helper in `ui/utils/formatters.py`
- [X] T028 [US3] Implement `format_letter_grade()` helper in `ui/utils/formatters.py`
- [X] T029 [US3] Implement `format_feedback()` helper in `ui/utils/formatters.py`
- [X] T030 [US3] Implement per-criterion scores table in `ui/components/results.py`
- [X] T031 [US3] Implement final score card (total, percentage, letter grade) in `ui/components/results.py`
- [X] T032 [US3] Implement feedback expander with strengths, improvements, suggestions in `ui/components/results.py`
- [X] T033 [US3] Add "Export JSON" download button in `ui/components/results.py`
- [X] T034 [US3] Add "Copy Feedback" button using `st.code` with copy in `ui/components/results.py`
- [X] T035 [US3] Wire results component into `ui/app.py` main area (shown when grading complete)

**Checkpoint**: User Story 3 complete — teacher can review and export results

---

## Phase 6: User Story 4 — Backend Integration (Priority: P1-Critical)

**Goal**: Connect UI to ADK grading backend

**Independent Test**: Trigger grading and verify backend events flow to UI state

### Implementation for User Story 4

- [X] T036 [US4] Create `ui/services/grading.py` with imports from `capstone.agent`
- [X] T037 [US4] Implement `start_grading_session()` function to create/resume ADK session in `ui/services/grading.py`
- [X] T038 [US4] Implement `send_rubric()` function to validate rubric via Runner in `ui/services/grading.py`
- [X] T039 [US4] Implement `send_submission()` function to store submission in session state in `ui/services/grading.py`
- [X] T040 [US4] Implement `run_grading()` async generator to execute pipeline and yield events in `ui/services/grading.py`
- [X] T041 [US4] Implement `get_results()` function to fetch final grades and feedback in `ui/services/grading.py`
- [X] T042 [US4] Map backend events to UI state updates (current_step, grades, final_score, feedback) in `ui/app.py`
- [X] T043 [US4] Wire "Start Grading" button to call grading service functions in `ui/app.py`

**Checkpoint**: User Story 4 complete — UI fully connected to ADK backend

---

## Phase 7: User Story 5 — Error Handling and UX Polish (Priority: P2)

**Goal**: Handle errors gracefully and improve UX

**Independent Test**: Submit invalid rubric and verify error message appears; verify button states

### Implementation for User Story 5

- [X] T044 [US5] Add error message display when rubric validation fails in `ui/components/sidebar.py`
- [X] T045 [US5] Add error message display when submission is missing in `ui/components/sidebar.py`
- [X] T046 [US5] Add error message display when backend call fails in `ui/components/chat.py`
- [X] T047 [US5] Disable "Start Grading" button when rubric_valid=false in `ui/components/sidebar.py`
- [X] T048 [US5] Disable "Start Grading" button when submission_text is null in `ui/components/sidebar.py`
- [X] T049 [US5] Add `st.spinner` loading indicator during grading in `ui/components/chat.py`
- [X] T050 [US5] Add rubric status badge (✅ Valid / ❌ Invalid) in `ui/app.py` status panel
- [X] T051 [US5] Add submission status badge (✅ Loaded / ⚠️ Empty) in `ui/app.py` status panel

**Checkpoint**: User Story 5 complete — errors handled, UX polished

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements across all components

- [X] T052 Update `specs/1-streamlit-grading-ui/quickstart.md` with actual usage instructions
- [X] T053 Add inline comments to `ui/services/grading.py` explaining ADK integration
- [X] T054 Verify all `st.session_state` keys are initialized before use
- [X] T055 Run full grading flow end-to-end and fix any integration issues
- [X] T056 Update `README.md` with Streamlit UI section

**Checkpoint**: Feature complete and documented

---

## Integration Sprint: ADK Backend + Approval Flow (New)

**Purpose**: Substitute the simulation by the real Runner and implement HITL approval

- [ ] I001 Connect `run_grading()` to `runner/grading_app` (rubric + submission) in `ui/services/grading.py`
- [ ] H001 Hotfix: stabilize graders (limit concurrency; retry per criterion with backoff; repair/validate JSON of `CriterionGrade`; if retries are exhausted, mark criterion error without derailing the flow and WITHOUT accepting fallback that degrades quality — must re-execute the criterion to obtain valid output)
- [ ] I002 Map events from Runner → `st.session_state` (steps, criteria, final_score, feedback, errors)
- [ ] I003 Handle Runner failures/timeouts with error messages in UI
- [ ] I004 Adjust `start_grading()` in `ui/app.py` to consume real events (without altering UX)
- [ ] I005 Implement approval modal/flow (<50% or >90%) with confirm/adjust grade
- [ ] I006 E2E test with real rubric/submission (validate states, messages, and results)
- [ ] T1007 Delete legacy code (final cleanup)
- [ ] TTEST01 [P] Cobrir H001/I002 com unit tests (parse/repair JSON, retries por critério) em `tests/`
- [ ] OAI01 Criar `services/openai_client.py` com LiteLLM (config por env `OPENAI_API_KEY`, `OPENAI_BASE_URL` opcional; helper `generate_json`)
- [ ] OAI02 Permit toggle de provider (Gemini/OpenAI) nos graders e pipeline (sem degradar H001/I002)
- [ ] OAI03 Documentar uso do provider OpenAI em README/quickstart e `.env.example`
- [ ] OAI04 Tests: unit tests for `openai_client` (mock LiteLLM) and smoke tests of graders with OpenAI provider

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─────────────────────────────────────────────────────────►
                 │
                 ▼
Phase 2 (Foundational) ──────────────────────────────────────────────────►
                 │
                 ├──────────────────┬──────────────────┬─────────────────┐
                 ▼                  ▼                  ▼                 ▼
         Phase 3 (US1)      Phase 4 (US2)      Phase 5 (US3)     Phase 6 (US4)
         Setup/Upload       Progress View      Results View      Backend
                 │                  │                  │                 │
                 └──────────────────┴──────────────────┴─────────────────┘
                                           │
                                           ▼
                                   Phase 7 (US5)
                                   Error Handling
                                           │
                                           ▼
                                   Phase 8 (Polish)
```

### User Story Dependencies

- **US1 (Setup)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (Progress)**: Can start after Phase 2 — Independent of US1
- **US3 (Results)**: Can start after Phase 2 — Independent of US1/US2
- **US4 (Backend)**: Can start after Phase 2 — Should complete before US5
- **US5 (Errors)**: Depends on US1, US2, US4 being substantially complete

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:

```bash
# Phase 1 parallel tasks:
T001, T002, T003, T004 — all create independent files

# Phase 3 (US1) parallel tasks:
T009, T010 — rubric upload methods (same file but independent sections)
T012, T013 — submission upload methods (same file but independent sections)

# Phase 5 (US3) parallel tasks:
T027, T028, T029 — formatter helpers (same file but independent functions)
```

---

## Implementation Strategy

### MVP First (Recommended)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 6: Backend Integration (US4) — critical path
4. Complete Phase 3: User Story 1 (Setup/Upload)
5. **STOP and VALIDATE**: Test rubric upload → grading → results flow
6. Continue with US2, US3, US5 as needed

### Task Count Summary

| Phase           | Story          | Task Count   |
| --------------- | -------------- | ------------ |
| Phase 1         | Setup          | 4            |
| Phase 2         | Foundational   | 3            |
| Phase 3         | US1 - Setup    | 11           |
| Phase 4         | US2 - Progress | 7            |
| Phase 5         | US3 - Results  | 10           |
| Phase 6         | US4 - Backend  | 8            |
| Phase 7         | US5 - Errors   | 8            |
| Phase 8         | Polish         | 5            |
| **Total** |                | **56** |

---

## Notes

- [P] tasks = different files or independent sections, no blocking dependencies
- [US#] label maps task to specific user story for traceability
- Each user story should be independently testable after completion
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
