# Data Model: Smart Grading Streamlit UI

**Feature**: SmartGradingStreamlitUI  
**Date**: 2025-12-10  
**Source**: [spec.md](./spec.md) Section 8 (Key Entities)

---

## 1. Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     Rubric      │       │   Submission    │
├─────────────────┤       ├─────────────────┤
│ name: str       │       │ text: str       │
│ description: str│       │ file_type: str  │
│ criteria: []    │───┐   │ length: int     │
│ total_points: int│   │   └────────┬────────┘
└─────────────────┘   │            │
                      │            │
                      ▼            ▼
              ┌───────────────────────────┐
              │     GradingSession        │
              ├───────────────────────────┤
              │ id: str                   │
              │ rubric: Rubric            │
              │ submission: Submission    │
              │ status: SessionStatus     │
              │ created_at: datetime      │
              │ updated_at: datetime      │
              └───────────┬───────────────┘
                          │
                          │ 1:N
                          ▼
              ┌───────────────────────────┐
              │     CriterionGrade        │
              ├───────────────────────────┤
              │ criterion_name: str       │
              │ score: float              │
              │ max_score: int            │
              │ evaluation_notes: str     │
              └───────────────────────────┘
                          │
                          │ N:1
                          ▼
              ┌───────────────────────────┐
              │    AggregationResult      │
              ├───────────────────────────┤
              │ total_score: float        │
              │ max_possible: float       │
              │ percentage: float         │
              │ letter_grade: str         │
              │ requires_approval: bool   │
              │ approval_reason: str?     │
              └───────────┬───────────────┘
                          │
                          │ 1:1
                          ▼
              ┌───────────────────────────┐
              │        Feedback           │
              ├───────────────────────────┤
              │ strengths: list[str]      │
              │ improvements: list[str]   │
              │ suggestions: list[str]    │
              │ encouragement: str        │
              │ overall_summary: str      │
              └───────────────────────────┘
```

---

## 2. Entity Definitions

### 2.1 Rubric

Grading criteria definition provided by teacher.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | Non-empty, max 200 chars |
| `description` | string | No | Max 1000 chars |
| `criteria` | Criterion[] | Yes | At least 1 criterion |
| `total_points` | int | Computed | Sum of criteria max_score |

**Source**: `examples/rubrics/*.json`, teacher input

### 2.2 Criterion

Single evaluation criterion within a rubric.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | Non-empty, max 100 chars |
| `description` | string | Yes | Non-empty, max 500 chars |
| `max_score` | int | Yes | > 0 |
| `slug` | string | Computed | Slugified name, unique within rubric |

**Validation Rules**:
- `max_score` must be positive integer
- `slug` auto-generated from `name` if not provided

### 2.3 Submission

Student work to be graded.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `text` | string | Yes | Non-empty |
| `file_type` | string | No | One of: py, txt, md, json |
| `length` | int | Computed | Character count |

**Source**: File upload or text paste

### 2.4 GradingSession

One grading workflow instance.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `id` | string | Yes | UUID format |
| `rubric` | Rubric | Yes | Valid rubric |
| `submission` | Submission | Yes | Valid submission |
| `status` | SessionStatus | Yes | Enum value |
| `grades` | CriterionGrade[] | No | Populated during grading |
| `aggregation` | AggregationResult | No | Populated after grading |
| `feedback` | Feedback | No | Populated after grading |
| `created_at` | datetime | Yes | Auto-set |
| `updated_at` | datetime | Yes | Auto-updated |

**State Transitions**:
```
idle → validating → grading → aggregating → feedback → complete
                 ↘ error (recoverable)
```

### 2.5 SessionStatus (Enum)

| Value | Description |
|-------|-------------|
| `idle` | Session created, no action taken |
| `validating` | Rubric validation in progress |
| `grading` | Criterion graders running |
| `aggregating` | Score aggregation in progress |
| `feedback` | Feedback generation in progress |
| `pending_approval` | Waiting for teacher approval |
| `complete` | Grading finished |
| `error` | Error occurred (recoverable) |

### 2.6 CriterionGrade

Score for one criterion.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `criterion_name` | string | Yes | Matches criterion in rubric |
| `score` | float | Yes | 0 ≤ score ≤ max_score |
| `max_score` | int | Yes | From criterion definition |
| `evaluation_notes` | string | Yes | Non-empty justification |

**Source**: `models/schemas.py::CriterionGrade`

### 2.7 AggregationResult

Final grade calculation.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `total_score` | float | Yes | Sum of criterion scores |
| `max_possible` | float | Yes | Sum of max_scores |
| `percentage` | float | Yes | 0 ≤ percentage ≤ 100 |
| `letter_grade` | string | Yes | One of: A, B, C, D, F |
| `requires_approval` | bool | Yes | True if < 50% or > 90% |
| `approval_reason` | string | Conditional | Required if requires_approval |

**Letter Grade Mapping**:
| Percentage | Grade |
|------------|-------|
| ≥ 90% | A |
| ≥ 80% | B |
| ≥ 70% | C |
| ≥ 60% | D |
| < 60% | F |

**Source**: `models/schemas.py::AggregationResult`

### 2.8 Feedback

Generated student feedback.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `strengths` | string[] | Yes | At least 1 item |
| `improvements` | string[] | Yes | At least 1 item |
| `suggestions` | string[] | Yes | At least 1 item |
| `encouragement` | string | Yes | Non-empty |
| `overall_summary` | string | Yes | Non-empty |

**Source**: `models/schemas.py::FinalFeedback`

---

## 3. UI State Model

State stored in `st.session_state` (display only, not persisted).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `setup_complete` | bool | False | Initial setup done |
| `rubric_json` | str \| None | None | Raw rubric JSON |
| `rubric_valid` | bool | False | Rubric passed validation |
| `rubric_errors` | list[str] | [] | Validation error messages |
| `submission_text` | str \| None | None | Raw submission text |
| `submission_preview` | str | "" | First 500 chars |
| `grading_session_id` | str \| None | None | ADK session ID |
| `grading_in_progress` | bool | False | Grading running |
| `current_step` | str | "idle" | Current pipeline step |
| `grades` | dict | {} | Per-criterion grades |
| `final_score` | dict \| None | None | Aggregation result |
| `feedback` | dict \| None | None | Generated feedback |
| `messages` | list[dict] | [] | Chat message history |
| `pending_approval` | bool | False | Approval required |
| `approval_reason` | str \| None | None | Why approval needed |
| `error_message` | str \| None | None | Current error |

---

## 4. Existing Backend Models

The following Pydantic models already exist in `models/schemas.py`:

- `CriterionGrade` — matches Section 2.6
- `AggregationResult` — matches Section 2.7
- `FinalFeedback` — matches Section 2.8
- `GradingError` — error response structure

**No new backend models required for MVP.**

---

## 5. Data Flow

```
Teacher Input                    Backend (ADK)                    UI Display
─────────────                    ─────────────                    ──────────
Rubric JSON    ──────────────►   RubricValidatorAgent   ──────►   Validation Status
Submission     ──────────────►   save_submission()      ──────►   Submission Preview
                                        │
                                        ▼
                                 ParallelGraders        ──────►   Per-Criterion Scores
                                        │
                                        ▼
                                 AggregatorAgent        ──────►   Final Score
                                        │
                                        ▼
                                 ApprovalAgent          ──────►   Approval Modal (if needed)
                                        │
                                        ▼
                                 FeedbackGeneratorAgent ──────►   Feedback Panel
```
