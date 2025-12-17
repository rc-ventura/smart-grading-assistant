# Feature Specification: Smart Grading Streamlit UI v2 (UX Overhaul)

**Component Name:** SmartGradingStreamlitUIv2
**Version:** 2.0.0
**Status:** Draft
**Created:** 2025-12-16

---

## 1. Overview

### 1.1 Description

A UI/UX overhaul of the existing Streamlit grading application to make the primary experience chat-first (ChatGPT-like), non-blocking during grading, and easier to navigate via tabs for Chat, Results, and Debug information.

This spec builds on the existing ADK Runner integration and focuses on presentation, interaction flow, and reliability of repeated grading runs.

### 1.2 Goals

- Provide a chat-first grading experience where progress and updates appear incrementally (no “frozen” UI).
- Organize the app using tabs: **Chat**, **Results**, **Debug**.
- Improve the perceived responsiveness during grading (clear progress, incremental events, friendly status).
- Allow repeated grading runs without restarting Streamlit (avoid “backend closed” / stale session errors).
- Keep backend (ADK) as the canonical source of grading state.

### 1.3 Non-Goals (Out of Scope)

- Changing core grading logic/agents output semantics.
- Adding authentication or multi-tenant deployments.
- Student-facing UI.

---

## 2. Actors

| Actor | Description |
| --- | --- |
| **Teacher** | Uses the UI to upload rubric/submission, trigger grading, monitor progress, review results, and optionally approve edge-case grades |

---

## 3. User Scenarios & Acceptance Criteria

### 3.1 Scenario: Chat-first, non-blocking grading

**As a** teacher
**I want to** start grading and see incremental progress updates
**So that** I never feel the app is frozen and I can understand what is happening

**Acceptance Criteria:**

- [ ] UI shows immediate feedback after “Start grading” (spinner/progress indicator within < 1s).
- [ ] Runner events are surfaced incrementally in the chat (no sudden “dump” at the end).
- [ ] Per-criterion progress/updates appear as each criterion completes.
- [ ] Errors are shown as actionable messages with recovery paths.

### 3.2 Scenario: Tabs for navigation

**As a** teacher
**I want to** navigate between Chat, Results and Debug
**So that** results and troubleshooting don’t clutter the main chat experience

**Acceptance Criteria:**

- [ ] App has tabs: **Chat**, **Results**, **Debug**.
- [ ] Results render only in the Results tab (or summarized in Chat, with a link/CTA).
- [ ] Debug tab can show raw Runner events/state deltas (optional toggle).

### 3.3 Scenario: Regrade without restarting Streamlit

**As a** teacher
**I want to** grade a new submission after finishing one
**So that** I can use the app continuously without restarting the process

**Acceptance Criteria:**

- [ ] After a run completes (success or error), the user can start a new run without restarting Streamlit.
- [ ] Any “backend closed” errors are handled by recreating the session/runner wiring as needed.
- [ ] UI state reset is predictable (no stale flags/messages leaking into the next run).

### 3.4 Scenario: Cancel grading

**As a** teacher
**I want to** cancel a grading run
**So that** I can stop long runs and recover quickly

**Acceptance Criteria:**

- [ ] UI offers “Cancel grading” while a run is in progress.
- [ ] Cancel stops consuming Runner events and resets UI to a safe state.
- [ ] Cancellation does not require restarting Streamlit.

### 3.5 Scenario: Human-in-the-Loop approval (migrated)

**As a** teacher
**I want to** approve edge-case grades
**So that** I can ensure fairness for failing/excellent submissions

**Acceptance Criteria:**

- [ ] UI shows approval modal when grade is < 50% or > 90%.
- [ ] Modal displays the reason for requiring approval.
- [ ] Teacher can accept the grade as-is or adjust it.
- [ ] Decision is sent back to backend for finalization.

### 3.6 Scenario: Debugging / observability

**As a** developer/teacher
**I want to** inspect raw backend events
**So that** I can troubleshoot unexpected behavior

**Acceptance Criteria:**

- [ ] Debug tab can display a chronological event log.
- [ ] Debug tab can optionally show raw Runner event payloads/state deltas.
- [ ] Debug tab can export/download the event log.

---

## 4. Functional Requirements

### 4.1 Layout

#### 4.1.1 Tabs

| Tab | Purpose | Contents |
| --- | --- | --- |
| **Chat** | Primary experience | Chat history, progress indicator, per-criterion updates, start/cancel actions |
| **Results** | Review output | Scores table, final score summary, feedback rendering, export actions |
| **Debug** | Troubleshoot | Raw events/state deltas (toggle), event log, diagnostics |

#### 4.1.2 Sidebar (optional)

If kept, the sidebar should focus on inputs (rubric/submission) and session metadata. Primary actions may also be surfaced in the Chat tab to reduce user context switching.

### 4.2 Event Streaming UX

- The UI should render a stable “progress shell” immediately when grading starts.
- Events should update existing UI placeholders/containers (instead of re-rendering large blocks abruptly).
- Reduce noise/duplication (one start + one completion per step).

### 4.3 Session Lifecycle

- Clearly define when to reuse vs recreate `grading_session_id`.
- Ensure finishing a run fully resets transient runtime state (`grading_in_progress`, pending confirmations, temporary buffers).
- Ensure the UI can recover from closed backends by recreating sessions.

---

## 5. Non-Functional Requirements

### 5.1 Performance

- UI must not appear frozen during grading.
- First visual feedback after start should appear quickly (< 1s perceived).

### 5.2 Reliability

- New runs should work without restarting Streamlit.
- Failure states should not poison subsequent runs.

### 5.3 Observability

- Debug outputs must be optional (off by default).
- Errors should include enough context to diagnose (without exposing secrets).

---

## 6. Success Criteria

| Criterion | Measurement | Target |
| --- | --- | --- |
| Non-blocking UX | User sees progress while grading | Always |
| Regrade reliability | User can run multiple sessions without restart | Always |
| Clarity | User can find results without scrolling chat | Tabs + clear summaries |

---

## 7. Open Questions

None yet.
