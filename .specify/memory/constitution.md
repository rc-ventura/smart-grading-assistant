<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (MAJOR: Initial constitution creation)
Modified principles: N/A (new document)
Added sections:
  - Purpose
  - Core Principles (5 principles)
  - Tech Stack & Conventions
  - AI Usage Rules
  - Testing & Quality
  - Streamlit UI Principles
  - Phases & Scope
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section exists)
  - .specify/templates/spec-template.md ✅ (compatible)
  - .specify/templates/tasks-template.md ✅ (compatible)
Follow-up TODOs: None
-->

# Smart Grading Assistant Constitution

## 1. Purpose

This project implements the **Smart Grading Assistant**, a teacher-facing application that:
- Uses AI agents (Google ADK) to grade student work using rubrics.
- Provides clear, explainable feedback for each criterion.
- Keeps teachers in control via human-in-the-loop approval.
- Prioritizes **reliability, safety, and usability** over "clever prompts".

**Non-goals:**
- This is NOT a generic chat UI.
- This is NOT a student-facing product (for now).
- This is NOT meant to bypass teacher judgment or local grading policies.

## 2. Core Principles

### I. Spec-Driven Development (SDD) First

Every non-trivial feature MUST start with a SPEC under `specs/`.
Implementation MUST follow: SPEC → PLAN → TASKS → IMPLEMENTATION.
No "vibe coding" large features directly from prompts.

**Rationale:** Ensures traceability, reduces rework, and maintains architectural consistency.

### II. Backend Owns Canonical Grading State

ADK runner + session service are the source of truth for grading.
Streamlit MUST hold only UI/display state (`st.session_state`).
UI MUST NOT duplicate backend logic or store canonical grades.

**Rationale:** Single source of truth prevents data inconsistencies and simplifies debugging.

### III. Teacher Trust Over Raw AI Power

All outputs MUST be explainable, traceable, and adjustable.
Human-in-the-loop approval MUST be respected where defined (scores < 50% or > 90%).
Teachers MUST be able to override or adjust any AI-generated grade.

**Rationale:** Builds trust, ensures accountability, and respects professional judgment.

### IV. Security & Privacy

No arbitrary filesystem access from UI or agents.
Student submissions and rubrics MUST be handled with least-privilege access.
No sending data to external services beyond the configured LLM/ADK provider.
API keys MUST NOT be hardcoded or exposed in logs.

**Rationale:** Protects student data and maintains compliance with privacy expectations.

### V. Clarity Over Cleverness

Code MUST be simple, explicit, and well-structured.
Prefer readability to premature optimization.
Avoid introducing new major frameworks without a SPEC and design discussion.

**Rationale:** Maintainability and onboarding speed outweigh micro-optimizations.

## 3. Tech Stack & Conventions

| Aspect | Standard |
|--------|----------|
| Language | Python 3.11+ |
| UI Framework | Streamlit |
| Backend Grading | Google ADK agents (`grading_app` / `runner`) |
| Persistence (MVP) | SQLite via `DatabaseSessionService` |
| Persistence (Later) | PostgreSQL |
| Async | Use async where required by ADK; keep UI integration simple |

**Code Conventions:**
- Use type hints on all public functions.
- Follow PEP 8; prefer tools like `ruff`/`black` if configured.
- Avoid introducing new major frameworks without a SPEC and design discussion.

## 4. AI Usage Rules

1. All large changes MUST go through:
   - `/speckit.specify` → define SPEC
   - `/speckit.plan` → define architecture/approach
   - `/speckit.tasks` → break into tasks
   - `/speckit.implement` → implement

2. LLMs MUST obey the SPEC:
   - Do NOT change requirements on the fly.
   - If the SPEC is unclear, propose SPEC edits instead of guessing.

3. No direct "make it better" refactors on the whole codebase:
   - Refactors MUST be tied to a SPEC or explicit task.

4. Do NOT weaken security or validation logic to "make it work".

## 5. Testing & Quality

**Minimum expectations:**
- For each non-trivial service (e.g., `services/grading.py`), add unit tests or integration tests.

**Critical flows requiring tests:**
- Rubric validation
- Grading pipeline wiring
- Mapping backend events → UI state

**Test guidelines:**
- Avoid brittle tests that depend on specific LLM wording.
- Test structure and contracts instead of exact outputs.

## 6. Streamlit UI Principles

**Sidebar** is used for:
- Setup (rubric + submission upload)
- Quick actions (Start Grading, Reset)
- Session info

**Main area** is used for:
- Grading/chat interaction
- Progress feedback
- Results + feedback display

**UI MUST:**
- Surface rubric status (valid/invalid with errors).
- Surface submission status (loaded/empty).
- Prevent "Start Grading" when preconditions are not met.
- Make final results easy to understand at a glance.

## 7. Phases & Scope

| Phase | Scope |
|-------|-------|
| **Phase 1 — Core Grading UI (MVP)** | Connect Streamlit UI to existing grading backend. Single-teacher flows, no authentication. |
| **Phase 2 — Enhanced UX** | Rubric management, better submission previews, human-in-the-loop UI. |
| **Phase 3 — RAG Rubric Assistant** | AI-assisted rubric creation and improvement. |
| **Phase 4 — Production Hardening** | Auth, proper DB, deployment, monitoring, analytics. |

Each phase SHOULD be broken into SPECs and tasks instead of big-bang changes.

## 8. Governance

- All SPECs, plans, and tasks live under `specs/` and are versioned with Git.
- Changes to critical SPECs (grading behavior, security, data handling) SHOULD go through PR review.
- If implementation diverges from SPEC, fix the implementation OR update the SPEC explicitly (with commit message explaining why).
- This constitution supersedes all other practices when conflicts arise.
- Amendments require documentation, approval, and migration plan if breaking.

**Version**: 1.0.0 | **Ratified**: 2025-12-10 | **Last Amended**: 2025-12-10
