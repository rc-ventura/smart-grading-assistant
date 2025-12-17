# Feature Specification: Smart Grading Streamlit UI

**Component Name:** SmartGradingStreamlitUI
**Version:** 1.0.0
**Status:** In Progress (UI implemented; backend integration currently simulated)
**Created:** 2025-12-10

---

## 1. Overview

### 1.1 Description

Streamlit-based teacher-facing UI for the Smart Grading Assistant. Connects to an existing ADK-based grading backend, orchestrates rubric upload, submission upload, grading requests, and feedback display.

### 1.2 Goals

- Provide an intuitive grading UI for teachers
- Connect to the existing multi-agent grading pipeline (ADK runner)
- Keep grading state in the backend; UI only holds display/session state
- Be ready for future RAG-based rubric assistant features

### 1.3 Non-Goals (Out of Scope)

- Student-facing UI or student login
- Backend agent logic changes
- Mobile native app
- Real-time collaboration between multiple teachers

---

## 2. Actors

| Actor             | Description                                                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Teacher** | Uses the UI to upload rubrics and submissions, trigger grading, review results and feedback, and approve or adjust grades |

---

## 3. User Scenarios & Acceptance Criteria

### 3.1 Scenario: Setup and Start Grading

**As a** teacher
**I want to** upload a rubric and student submission
**So that** I can start the automated grading process

**Acceptance Criteria:**

- [X] Teacher can upload rubric via file upload OR text paste
- [X] Teacher can upload submission via file upload OR text paste
- [ ] UI displays validation status for rubric (valid/invalid with errors)
- [ ] UI displays submission status (loaded with preview)
- [ ] "Start Grading" button is enabled only when rubric is valid AND submission is loaded
- [ ] Teacher can reset the session and start over

### 3.2 Scenario: View Grading Progress

**As a** teacher
**I want to** see the grading progress in real-time
**So that** I know the system is working and can estimate completion time

**Acceptance Criteria:**

- [ ] UI shows current step indicator (validating → grading → aggregating → feedback)
- [ ] Per-criterion scores appear as each grader completes
- [ ] Final score and letter grade are displayed after aggregation
- [ ] Progress is visible within a few seconds of starting

### 3.3 Scenario: Review Results and Feedback

**As a** teacher
**I want to** review the detailed grading results and generated feedback
**So that** I can verify accuracy before sharing with the student

**Acceptance Criteria:**

- [ ] UI displays per-criterion scores with evaluation notes
- [ ] UI displays final score, percentage, and letter grade
- [ ] Feedback panel shows strengths, areas for improvement, and suggestions
- [ ] Teacher can expand/collapse the feedback panel
- [ ] Teacher can export results as JSON or copy feedback to clipboard

### 3.4 Scenario: Human-in-the-Loop Approval

**As a** teacher
**I want to** be prompted to approve edge-case grades
**So that** I can ensure fairness for exceptional or failing submissions

**Acceptance Criteria:**

- [ ] UI shows approval modal when grade is < 50% or > 90%
- [ ] Modal displays the reason for requiring approval
- [ ] Teacher can accept the grade as-is
- [ ] Teacher can adjust the grade before finalizing
- [ ] Decision is sent back to backend for finalization

### 3.5 Scenario: Session Management (Phase 2+)

**As a** teacher
**I want to** view and resume past grading sessions
**So that** I can continue incomplete work or review previous grades

**Acceptance Criteria:**

- [ ] UI lists past grading sessions with summary info
- [ ] Teacher can select a session to view details
- [ ] Teacher can resume an incomplete session

---

## 4. Functional Requirements

### 4.1 UI Layout

#### 4.1.1 Sidebar

| Element                    | Description                                                      |
| -------------------------- | ---------------------------------------------------------------- |
| **Rubric Input**     | File upload (.json) or text area for pasting rubric JSON         |
| **Submission Input** | File upload (.py, .txt, .md) or text area for pasting submission |
| **Quick Actions**    | "Start Grading" and "Reset" buttons                              |
| **Session Info**     | Display current session ID and status                            |

#### 4.1.2 Main Area

| Section                      | Elements                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| **Status Panel**       | Rubric status badge, Submission status badge                                         |
| **Chat/Grading Panel** | Message history, grading progress indicators, input box                              |
| **Results Panel**      | Per-criterion scores, final score, letter grade, expandable feedback, export buttons |

### 4.2 UI State Management

All UI state is stored in `st.session_state`:

| Key                     | Type          | Default | Description                                              |
| ----------------------- | ------------- | ------- | -------------------------------------------------------- |
| `setup_complete`      | boolean       | false   | Whether initial setup is done                            |
| `rubric_json`         | string\| null | null    | Raw rubric JSON string                                   |
| `rubric_valid`        | boolean       | false   | Whether rubric passed validation                         |
| `submission_text`     | string\| null | null    | Raw submission text                                      |
| `grading_session_id`  | string\| null | null    | ADK session ID                                           |
| `grading_in_progress` | boolean       | false   | Whether grading is running                               |
| `current_step`        | string        | "idle"  | One of: idle, validating, grading, aggregating, feedback |
| `grades`              | object        | {}      | Per-criterion grade results                              |
| `final_score`         | number\| null | null    | Final aggregated score                                   |
| `feedback`            | string\| null | null    | Generated feedback text                                  |
| `messages`            | array         | []      | Chat message history for display                         |
| `pending_approval`    | boolean       | false   | Whether approval is required                             |
| `approval_reason`     | string\| null | null    | Reason for requiring approval                            |

### 4.3 Backend Integration

#### 4.3.1 Integration Type

Direct integration with ADK Runner via Python imports:

```
Module: capstone.agent.grading_app
Services:
  - runner: orchestrates multi-agent grading pipeline
  - session_service: manages ADK sessions (SQLite or DB)
```

**Current implementation status:** UI wiring is complete; `ui/services/grading.py` is using a simulated pipeline for now. To meet the full integration requirement, replace the simulation with `runner`/`grading_app` calls and stream events into `st.session_state`.

#### 4.3.2 Backend Responsibilities

- Validate rubrics via RubricValidatorAgent
- Run grading agents (ParallelGraders)
- Aggregate scores via AggregatorAgent
- Generate feedback via FeedbackGeneratorAgent
- Persist grading sessions and results

#### 4.3.3 UI Responsibilities

- Collect rubric and submission from teacher
- Send requests to backend via Runner
- Display progress and results
- Handle human-in-the-loop approval flow
- Manage display state only (backend owns canonical state)

### 4.4 Flows

#### 4.4.1 Setup Flow

1. Teacher uploads rubric (file or paste)
2. UI parses and stores rubric JSON in state
3. Backend validates rubric via Runner
4. UI updates rubric status display
5. Teacher uploads submission (file or paste)
6. UI updates submission status display

#### 4.4.2 Grading Flow

**Preconditions:** rubric_valid == true AND submission_text is not null

1. UI triggers grading via services/grading bridge
2. Backend runs multi-agent pipeline
3. UI streams or polls events from Runner
4. UI updates progress indicators
5. UI updates per-criterion scores as they complete
6. UI updates final score and letter grade
7. UI populates feedback panel

#### 4.4.3 Human-in-the-Loop Flow

1. Backend emits approval_required event
2. UI sets pending_approval = true
3. UI shows modal with reason
4. Teacher accepts or adjusts grade
5. UI sends decision back to backend
6. Backend finalizes result

---

## 5. Non-Functional Requirements

### 5.1 Performance

- Must handle typical grading sessions without freezing UI
- Grading progress should be visible within a few seconds of starting
- Streaming preferred over polling for responsiveness

### 5.2 User Experience

- Teacher must be able to start a grading session with ≤ 3 main actions
- Per-criterion scores and final score must be clearly visible
- Error states must be clearly communicated with recovery options

### 5.3 Observability

- Log key UI-backend interactions (start grading, errors)
- Display meaningful error messages from backend

### 5.4 Constraints

- Backend (ADK) owns canonical grading state
- Streamlit UI must not duplicate backend logic
- RubricGuardrailPlugin must be honored: no grading without valid rubric
- Only teacher-facing UI is required; no student login at this stage
- Initial MVP can use in-memory or SQLite; later phases may use Postgres

---

## 6. Success Criteria

| Criterion       | Measurement                                     | Target                                    |
| --------------- | ----------------------------------------------- | ----------------------------------------- |
| Task Completion | Teacher can complete full grading flow          | 100% of test scenarios pass               |
| Time to Grade   | From "Start Grading" to results displayed       | < 30 seconds for typical submission       |
| Error Recovery  | Teacher can recover from errors without restart | All error states have clear recovery path |
| Usability       | Actions to start grading                        | ≤ 3 main actions                         |
| Clarity         | Teacher understands grade breakdown             | All scores visible with justification     |

---

## 7. Phase Roadmap

### Phase 1: Core Grading UI (MVP)

- Sidebar with rubric/submission upload
- Main chat/grading interface
- Progress indicators
- Results and feedback display
- Basic error handling

### Phase 2: Enhanced UX & Rubric Management

- Rubric preview and inline editing
- Syntax highlighting for code submissions
- Human-in-the-loop approval modal
- Session history and resume

### Phase 3: RAG Rubric Assistant

- Knowledge base of rubric examples
- AI-powered rubric creation chat
- Rubric improvement suggestions

### Phase 4: Production Hardening & Deployment

- Authentication (Google OAuth)
- PostgreSQL for sessions
- Cloud Run deployment
- Analytics dashboard

---

## 8. Key Entities

| Entity                      | Description                   | Key Attributes                                           |
| --------------------------- | ----------------------------- | -------------------------------------------------------- |
| **Rubric**            | Grading criteria definition   | name, criteria[], total_points                           |
| **Criterion**         | Single evaluation criterion   | name, description, max_score, slug                       |
| **Submission**        | Student work to be graded     | text, file_type, length                                  |
| **GradingSession**    | One grading workflow instance | id, rubric, submission, status, results                  |
| **CriterionGrade**    | Score for one criterion       | criterion_name, score, max_score, notes                  |
| **AggregationResult** | Final grade calculation       | total_score, percentage, letter_grade, requires_approval |
| **Feedback**          | Generated student feedback    | strengths, improvements, suggestions                     |

---

## 9. Dependencies

| Dependency        | Type      | Description           |
| ----------------- | --------- | --------------------- |
| Streamlit         | Framework | UI framework          |
| google-genai      | Library   | Gemini API client     |
| capstone.agent    | Internal  | ADK grading pipeline  |
| capstone.services | Internal  | Gemini client helpers |

---

## 10. Assumptions

1. Teachers have basic familiarity with JSON rubric format
2. Submissions are text-based (code, essays) not binary files
3. Single teacher per session (no concurrent editing)
4. Backend ADK pipeline is stable and tested
5. Network connectivity to Gemini API is available

---

## 11. Open Questions

None at this time. All requirements are sufficiently specified for MVP implementation.
