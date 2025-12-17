# Implementation Plan: Smart Grading Streamlit UI

**Branch**: `1-streamlit-grading-ui` | **Date**: 2025-12-10 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/1-streamlit-grading-ui/spec.md`

---

## Summary

Build a Streamlit-based teacher-facing UI that connects to the existing ADK grading backend. The UI provides rubric and submission upload, triggers the multi-agent grading pipeline, displays real-time progress, and shows results with feedback. Human-in-the-loop approval is supported for edge cases.

Current status: the Streamlit UI is implemented and the grading service integrates with the real ADK Runner, streaming events into `st.session_state`. Remaining UX improvements are tracked in `/specs/2-streamlit-grading-ui-v2/`.

---

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Streamlit, google-genai, google-adk  
**Storage**: In-memory sessions (current), with a path to SQLite/PostgreSQL later  
**Testing**: pytest (existing tests under `capstone/tests/`)  
**Target Platform**: Web browser (localhost or deployed)  
**Project Type**: Web application (Streamlit frontend + ADK backend)  
**Performance Goals**: < 30 seconds from "Start Grading" to results  
**Constraints**: Backend owns state; UI is display-only; RubricGuardrailPlugin must be honored  
**Scale/Scope**: Single teacher per session; typical submissions < 1000 lines

---

## Constitution Check

*GATE: Constitution found at `.specify/memory/constitution.md`.*

- ✅ No unnecessary complexity introduced
- ✅ Single responsibility: UI handles display, backend handles grading
- ✅ Existing patterns reused (ADK Runner, session service)
- ✅ No new external dependencies beyond Streamlit

Notes:
- UX polish, improved streaming presentation, and regrade reliability are tracked as UI v2 work.
- Critical flows (Runner wiring + event → UI mapping) must have pytest coverage.

---

## Project Structure

### Documentation (this feature)

```text
specs/1-streamlit-grading-ui/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
ui/
├── app.py                    # Streamlit entrypoint (refactor existing)
├── components/
│   ├── __init__.py
│   ├── sidebar.py            # Rubric & submission setup, quick actions
│   ├── chat.py               # Chat/grading interaction area
│   └── results.py            # Results and feedback display
├── services/
│   ├── __init__.py
│   └── grading.py            # Bridge between UI and ADK runner
└── utils/
    ├── __init__.py
    └── formatters.py         # Formatting helpers for scores, feedback

tests/
├── test_ui_grading.py
├── test_calculate_score.py
└── ...
```

**Structure Decision**: Modular Streamlit app with components split by responsibility. Services layer bridges UI to existing ADK backend without duplicating logic.

---

## Phase 1: Core Grading UI (MVP)

### 1.1 Sidebar Setup (`ui/components/sidebar.py`)

| Task | Description | Acceptance |
|------|-------------|------------|
| Rubric file upload | `st.file_uploader` for .json files | File parsed and stored in state |
| Rubric text paste | `st.text_area` for JSON paste | JSON validated on input |
| Submission file upload | `st.file_uploader` for .py, .txt, .md | Content stored in state |
| Submission text paste | `st.text_area` for code/text | Content stored in state |
| Start Grading button | Enabled when rubric valid + submission loaded | Triggers grading flow |
| Reset button | Clears session state | Returns to initial state |
| Session info | Display session ID and current step | Always visible |

### 1.2 Main Chat Interface (`ui/components/chat.py`)

| Task | Description | Acceptance |
|------|-------------|------------|
| Message history | Display user/assistant messages | Scrollable chat view |
| Progress indicators | Show current step (validating/grading/etc) | Updates in real-time |
| Per-criterion scores | Display as each grader completes | Score + criterion name |
| Final score display | Show total, percentage, letter grade | Prominent display |
| Input box | Optional teacher input during grading | Functional but optional |

### 1.3 Backend Integration (`ui/services/grading.py`)

| Task | Description | Acceptance |
|------|-------------|------------|
| `start_grading_session()` | Create or resume ADK session | Returns session_id |
| `send_rubric()` | Send rubric to RubricValidatorAgent | Returns validation result |
| `send_submission()` | Store submission in session state | Returns confirmation |
| `run_grading()` | Execute grading pipeline | Yields events for UI |
| `get_results()` | Fetch final results from session | Returns grades + feedback |

### 1.4 Results Panel (`ui/components/results.py`)

| Task | Description | Acceptance |
|------|-------------|------------|
| Per-criterion table | Table with criterion, score, max, notes | All criteria shown |
| Final score card | Prominent display of total/percentage/letter | Clear and visible |
| Feedback expander | Expandable panel with full feedback | Strengths, improvements, suggestions |
| Export JSON | Download results as JSON file | Valid JSON with all data |
| Copy feedback | Copy feedback text to clipboard | One-click copy |

---

## Phase 1.5: ADK Backend Integration Sprint

Goal: completed — stream real Runner events into the existing UI without changing UX.

### 1.5.1 Runner Wiring (Session + Message Types)

- Ensure `ADK_AVAILABLE` is true when the backend is importable (fix any stale imports in `ui/services/grading.py`).
- Ensure `runner.run_async(...)` is called with the correct message type (`google.genai.types.Content`).
- Ensure session creation/resume is handled consistently (single `grading_session_id` per UI run).

### 1.5.2 Event Mapping (Runner → UI State)

- Implement `_map_runner_event(...)` to translate ADK `Event` objects into UI-friendly events:
  - step start/complete transitions
  - per-criterion grade updates
  - aggregation result updates (final_score)
  - feedback updates
  - errors (including per-criterion failures)
  - tool confirmations (pending approval)
- Ensure `st.session_state` updates are derived from Runner event state deltas (backend remains canonical).

### 1.5.3 UI Consumption (No UX Changes)

- Keep `ui/app.py` behavior the same (chat messages, progress indicator, results panel), but ensure it can consume the real mapped events.

### 1.5.4 Cleanup (After Runner Is Stable)

- Remove `_simulate_grading` and the simulation fallback path.
- Remove duplicate approval flag keys (standardize on `requires_human_approval`).
- Remove legacy or unused code that only exists to satisfy tests (as long as tests remain meaningful).

### 1.5.5 Tests

- Update `capstone/tests/test_ui_grading.py` to stop depending on the simulation flow.
- Add/adjust tests to validate:
  - Runner message typing (Content)
  - mapping of `state_delta` keys into `st.session_state`
  - tool confirmation → `pending_approval` behavior

---

## Phase 2: UX Enhancements

| Feature | Description |
|---------|-------------|
| Rubric preview | Show parsed rubric with criteria list |
| Rubric inline edit | Edit criteria in UI before grading |
| Load from examples | Select from `examples/rubrics/` |
| Syntax highlighting | Code submissions with highlighting |
| Line numbers | Show line numbers in submission preview |
| Approval modal | Modal for human-in-the-loop decisions |
| Session history | List and resume past sessions |

---

## Phase 3: RAG Rubric Assistant

| Feature | Description |
|---------|-------------|
| `services/rag/indexer.py` | Index rubrics and examples |
| `services/rag/retriever.py` | RAG retrieval for similar rubrics |
| `services/rag/assistant.py` | Rubric assistant agent |
| Rubric chat mode | Dedicated page for rubric creation |
| Rubric suggestions | AI-powered improvement suggestions |

---

## Phase 4: Production

| Feature | Description |
|---------|-------------|
| Authentication | Google OAuth for teacher login |
| PostgreSQL | Replace SQLite for production |
| Docker | Containerize application |
| Cloud Run | Deploy to GCP |
| Analytics | Grading metrics dashboard |

---

## Complexity Tracking

> No violations identified. Implementation follows existing patterns.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| State management | `st.session_state` for UI, ADK for backend | Clear separation of concerns |
| Backend integration | Direct Python imports | Simplest approach for MVP |
| Component structure | Separate files per component | Maintainability |

---

## Next Steps

1. Implement UX overhaul and stability fixes in `/specs/2-streamlit-grading-ui-v2/`
2. Implement approval modal/flow (migrated from the integration sprint)
3. Add/strengthen tests as needed (unit + optional automated E2E)
