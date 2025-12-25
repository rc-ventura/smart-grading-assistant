# Tasks: Optimized HIT Flow

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)
**Feature Branch**: `003-optimized-hit-flow`

## Phase 1: Aggregator Logic (Backend Flagging)

- [x] HIT-001 Update `AggregatorAgent` to check `final_score` against `FAILING_THRESHOLD` and `EXCEPTIONAL_THRESHOLD` from settings.
- [x] HIT-002 Update `AggregatorAgent` output schema (or tool return) to include `requires_human_intervention` (bool) and `anomaly_reason` (str).
- [x] HIT-003 Unit Test: Verify Aggregator sets flags correctly for low/high scores (`tests/test_aggregator_flags.py`).

## Phase 2: Pipeline Orchestration (Root & Flow)

- [x] HIT-004 Keep `GradingPipeline` sequential: `Graders -> Aggregator -> Approval -> Feedback`. Use ADK resumability to pause at Approval if needed.
- [x] HIT-005 Update `needs_approval()` to respect `aggregation_result.requires_human_intervention` as the primary gate (with legacy flags as fallback).
- [x] HIT-006 Integration Test: Verify pipeline order and approval gating (`tests/test_phase2_resumability.py`).

## Phase 3: UI Rejection & Manual Adjustment

- [x] HIT-007 Update `ui/components/approval.py` with three decisions: Approve / Manual Adjust / Regrade and dynamic button labels.
- [x] HIT-008 Implement "Manual Adjust" form (Score, Letter Grade, Feedback) and persist to session_state.
- [x] HIT-009 Update `ui/services/grading_execution.py` to handle "Manual Adjust": finalize immediately, skip FeedbackAgent, emit `grading_complete`.
- [x] HIT-010 Update `ui/services/grading_execution.py` to handle "Regrade": reset state and restart run from scratch.
- [x] HIT-011 Add chat events for approval actions (approval_action) and update consumer to log them.
- [x] HIT-012 Add unit tests for runner decisions (`tests/test_phase3_runner_decisions.py`).

## Phase 4: Feedback Consistency

- [x] HIT-013 Ensure `FeedbackGeneratorAgent` uses the *final* score (post-approval or post-manual-adjust) if it runs after approval.
- [x] HIT-014 E2E Test: Full flow from Low Score -> Approval -> Manual Adjust -> Feedback Generation.

## Phase 5: Cleanup

- [x] HIT-015 Verify no "orphaned" feedback generation (double feedback) occurs.
- [x] HIT-016 Final manual smoke test of all 3 paths (Pass, HIT-Approve, HIT-Reject-Adjust).
