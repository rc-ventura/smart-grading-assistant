# Implementation Plan - Optimized HIT Flow

**Feature**: Optimized HIT Flow (Aggregator-driven flags, Conditional Feedback)
**Status**: Draft
**Spec**: [spec.md](./spec.md)

## Architecture Changes

1.  **Orchestration Logic Shift**:
    - Move the orchestration of "What happens after aggregation" from a fixed `SequentialAgent` list to the `RootAgent` (or a smart controller).
    - **Current**: `Graders -> Aggregator -> Feedback -> Approval` (Sequential)
    - **New**:
        1. `GradingPipeline` executes `Graders -> Aggregator`.
        2. `RootAgent` inspects `aggregation_result`.
        3. **Conditional Branch**:
            - If `requires_human_intervention`: Transfer to `ApprovalAgent`.
            - Else: Transfer to `FeedbackGeneratorAgent`.
        4. **Post-Approval**:
            - If Approved/Manually Adjusted: Transfer to `FeedbackGeneratorAgent` (to generate feedback on the final score).
            - If Rejected (Regrade): Restart process.

2.  **Aggregator Responsibility**:
    - Now explicitly checks thresholds (`FAILING_THRESHOLD`, `EXCEPTIONAL_THRESHOLD`) and sets metadata flags (`requires_human_intervention`, `anomaly_reason`) in its output.

3.  **UI Responsibility (Rejection)**:
    - The UI must handle the "Reject" signal not just as a stop, but as a branching decision (Manual Adjust vs Regrade).

## Proposed Changes

### 1. Agents Configuration (`agents/`)

#### `agents/aggregator.py`
- Update `system_instruction` or `aggregate_grades` tool to:
    - Compare calculated score vs thresholds.
    - Add `requires_human_intervention: bool` to the output schema/dict.
    - Add `anomaly_reason: str` (e.g., "Score 45 < 60 (Failing)").

#### `agents/root.py`
- Modify `create_grading_pipeline`:
    - Remove `feedback` and `approval` from the `sub_agents` list.
    - Keep only `[graders, aggregator]`.
- Update `RootAgent` (or the coordination logic, if it resides in `orchestrator.py` or similar):
    - *Note*: Since ADK agents are often state-machine driven or sequential, we need to verify where the "transfer" logic lives. If `GradingPipeline` is just a `SequentialAgent`, it finishes after Aggregator.
    - The "Runner" loop in `grading_runner.py` or the `RootAgent` instructions might need adjustment to handle the hand-off.
    - *Actually*, `RootAgent` usually just routes. We might need a `OrchestratorAgent` or simply update the `RootAgent` instructions to: "First run GradingPipeline. Then check result. If flag set, call Approval. Else call Feedback."

### 2. UI / Runner Logic (`ui/services/`)

#### `ui/services/grading_runner.py`
- Handle the new flow events.
- If `ApprovalAgent` is called, UI shows the approval tab (existing logic, just triggered differently).
- Ensure `FeedbackGeneratorAgent` is invoked *after* approval if needed.
    - This might be automatic if the `RootAgent` is smart enough.
    - Or we might need to manually trigger the next step in `resume_runner_with_confirmation`.

### 3. UI Components (`ui/components/`)

#### `ui/components/approval.py`
- Implement the "Reject" Action UI:
    - SelectBox: "Manual Adjust" vs "Regrade".
    - Inputs for Manual Adjust (Score, Grade, Feedback override).
    - Button "Confirm Rejection Action".

### 4. Configuration (`config/settings.py`)
- Ensure `FAILING_THRESHOLD` and `EXCEPTIONAL_THRESHOLD` are accessible to Aggregator.

## Verification Plan

### Automated Tests
- **`tests/test_aggregator_flags.py`**:
    - Mock Grader output (low score).
    - Run Aggregator.
    - Assert `requires_human_intervention` is True.
    - Mock Grader output (mid score).
    - Assert `requires_human_intervention` is False.
- **`tests/test_pipeline_routing.py`**:
    - (Integration) Run full flow with Mock Graders.
    - Case A (Anomaly): Verify `ApprovalAgent` is the next active agent after `GradingPipeline`. Verify `FeedbackGenerator` did NOT run.
    - Case B (Normal): Verify `FeedbackGenerator` runs immediately after `GradingPipeline`.

### Manual Verification
1.  **Happy Path**: Upload submission, get 80%. Verify Feedback appears, no Approval request.
2.  **HIT Path**: Upload submission, get 40%. Verify Approval request. Verify NO feedback yet.
    - Approve -> Verify Feedback generates.
3.  **Rejection Path**:
    - Trigger HIT. Reject -> Manual Adjust to 70%.
    - Verify Feedback generates for 70%.
    - Verify Results tab shows 70%.
