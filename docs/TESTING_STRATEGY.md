# Testing Strategy: Optimized HIT Flow

## Overview

The Optimized HIT Flow uses a hybrid testing approach:

### 1. Unit/Integration Tests (Phases 1-3)
**Location**: `tests/test_phase*.py`
**Nature**: Mocked ADK runner, no real API calls
**Purpose**: Verify logic, state management, and event flow

- **test_phase2_resumability.py**: Tests pipeline order and approval gating
- **test_phase3_runner_decisions.py**: Tests runner handling of manual adjust/regrade
- **test_aggregator_flags.py**: Tests aggregator threshold logic
- **test_pipeline_routing.py**: Tests agent sequence

### 2. Phase 5 Tests
**Location**: `tests/test_phase5_double_feedback.py`
**Nature**: Fully mocked ADK runner, no real API calls
**Purpose**: Verify no double feedback generation across all approval paths

### 3. Smoke Tests (Manual)
**Location**: `docs/SMOKE_TEST_CHECKLIST.md`
**Nature**: Real Streamlit UI with live ADK runner
**Purpose**: End-to-end verification of user experience

## Test Environment Considerations

### CI/CD Environment
- No API key available
- Tests expect and handle API key errors gracefully
- Focus on logic verification, not LLM responses

### Development/Smoke Testing
- Requires valid API key
- Tests actual ADK runner behavior
- Verifies complete user flows

## Test Coverage Matrix

| Test Type | API Calls | Runner | Purpose |
|-----------|-----------|---------|---------|
| Unit Tests | Mocked | Mocked | Logic verification |
| Phase 5 Tests | Mocked | Mocked | Double feedback prevention |
| Smoke Tests | Real | Real | End-to-end UX validation |

## Key Test Scenarios

### Automated Tests Verify:
- Pipeline sequence: Graders → Aggregator → Approval → Feedback
- Approval gating based on `requires_human_intervention`
- Manual adjust skips feedback generation
- Regrade resets state properly
- Chat events emitted for all actions

### Smoke Tests Verify:
- UI renders correctly in browser
- Approval tab appears at right time
- Button labels update dynamically
- Manual overrides work as expected
- No visual glitches or state leaks
