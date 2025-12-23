# Tasks: Optimized HIT Flow

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)
**Feature Branch**: `003-optimized-hit-flow`

## Phase 1: Aggregator Logic (Backend Flagging)

- [ ] HIT-001 Update `AggregatorAgent` to check `final_score` against `FAILING_THRESHOLD` and `EXCEPTIONAL_THRESHOLD` from settings.
- [ ] HIT-002 Update `AggregatorAgent` output schema (or tool return) to include `requires_human_intervention` (bool) and `anomaly_reason` (str).
- [ ] HIT-003 Unit Test: Verify Aggregator sets flags correctly for low/high scores (`tests/test_aggregator_flags.py`).

## Phase 2: Pipeline Orchestration (Root & Flow)

- [ ] HIT-004 Modify `GradingPipeline` (in `agents/root.py`) to ONLY include `Graders` and `Aggregator`. Remove `Feedback` and `Approval` from the fixed sequence.
- [ ] HIT-005 Update `RootAgent` instructions (or `orchestrator` logic) to inspect `aggregation_result` from `GradingPipeline`.
    - If `requires_human_intervention` is True -> Call `ApprovalAgent`.
    - If False -> Call `FeedbackGeneratorAgent`.
- [ ] HIT-006 Integration Test: Verify correct routing (Mock Graders -> Aggregator -> [Check Next Agent]) (`tests/test_pipeline_routing.py`).

## Phase 3: UI Rejection & Manual Adjustment

- [ ] HIT-007 Update `ui/components/approval.py` to add "Reject Action" UI (Select: Manual Adjust / Regrade).
- [ ] HIT-008 Implement "Manual Adjust" form (Score, Grade, Feedback inputs).
- [ ] HIT-009 Update `ui/services/grading_runner.py` (resume logic) to handle "Manual Adjust":
    - Update session state directly.
    - Skip remaining ADK steps (or invoke Feedback if needed).
- [ ] HIT-010 Update `ui/services/grading_runner.py` to handle "Regrade":
    - Trigger `reset_grading_state` and restart.

## Phase 4: Feedback Consistency

- [ ] HIT-011 Ensure `FeedbackGeneratorAgent` uses the *final* score (post-approval or post-manual-adjust) if it runs after approval.
- [ ] HIT-012 E2E Test: Full flow from Low Score -> Approval -> Manual Adjust -> Feedback Generation.

## Phase 5: Cleanup

- [ ] HIT-013 Verify no "orphaned" feedback generation (double feedback) occurs.
- [ ] HIT-014 Final manual smoke test of all 3 paths (Pass, HIT-Approve, HIT-Reject-Adjust).
