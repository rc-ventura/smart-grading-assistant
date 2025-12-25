# Smoke Test Checklist: Optimized HIT Flow

**Purpose**: Manual verification of all three primary grading paths
**Location**: Streamlit UI (browser) - `http://localhost:8501`
**Created**: 2025-12-25
**Feature**: Optimized HIT Flow (003) - Human-in-the-Loop approval gating

## Setup Requirements

1. **Environment**: Working Streamlit app with valid API key
2. **Test Data**: 
   - Rubric with clear criteria
   - Submission text that will generate:
     - Normal score (60-80%) for Pass path
     - Low score (<50%) for HIT paths
3. **Browser**: Streamlit app running

## Test Paths

### Path 1: Pass (Normal Flow)
**Expected**: No approval UI, direct grading → feedback

1. **Input**: Rubric + submission that scores 75%
2. **Verify**:
   - [ ] Grading completes without interruption
   - [ ] No approval tab appears
   - [ ] Final score shows 75% (C/B grade)
   - [ ] Feedback is generated automatically
   - [ ] Chat shows normal grading flow
   - [ ] Results tab displays score and feedback

### Path 2: HIT-Approve (Low Score → Approve)
**Expected**: Approval UI → Approve → feedback

1. **Input**: Rubric + submission that scores 40%
2. **Verify**:
   - [ ] Grading pauses at approval step
   - [ ] Approval tab appears with "Approve" button
   - [ ] Anomaly reason explains low score
   - [ ] Click "Approve" → grading resumes
   - [ ] Chat shows "Grade approved" event
   - [ ] Feedback is generated after approval
   - [ ] Final score reflects original 40%

### Path 3: HIT-Reject-Manual Adjust (Low Score → Manual Adjust)
**Expected**: Approval UI → Manual Adjust → immediate completion

1. **Input**: Rubric + submission that scores 35%
2. **Verify**:
   - [ ] Grading pauses at approval step
   - [ ] Approval tab appears with rejection options
   - [ ] Select "Manual Adjust" radio
   - [ ] Enter manual score (85), letter (B), feedback
   - [ ] Button label changes to "Manual Adjust"
   - [ ] Click "Manual Adjust" → immediate completion
   - [ ] Chat shows "Grade manually adjusted" event
   - [ ] NO additional feedback generated (using manual feedback)
   - [ ] Final score shows manual 85%, B grade, manual feedback

### Path 4: HIT-Reject-Regrade (Low Score → Regrade)
**Expected**: Approval UI → Regrade → fresh grading cycle

1. **Input**: Rubric + submission that scores 30%
2. **Verify**:
   - [ ] Grading pauses at approval step
   - [ ] Approval tab appears with rejection options
   - [ ] Select "Regrade" radio
   - [ ] Button label changes to "Regrade"
   - [ ] Click "Regrade" → grading restarts from beginning
   - [ ] Chat shows "Grade regraded" event
   - [ ] New grading cycle runs (may hit approval again)
   - [ ] Previous approval state is cleared

## Edge Cases to Verify

- [ ] **Cancel**: Click cancel in approval UI → sets decision=cancelled
- [ ] **Session State Cleanup**: After each path, verify no leftover approval flags
- [ ] **Chat History**: All approval actions logged correctly
- [ ] **UI Consistency**: Button labels update dynamically
- [ ] **Error Recovery**: Handle API errors gracefully during approval

## Success Criteria

- [ ] All 3 primary paths complete successfully
- [ ] No double feedback generation
- [ ] UI state management is clean
- [ ] Chat events provide clear audit trail
- [ ] Manual adjust overrides work correctly
- [ ] Regrade truly restarts the process

## Notes

- Use debug toggle if available to force approval without threshold manipulation
- Each test should be done in a fresh browser session
- Verify Streamlit reruns don't cause approval loops
- Check browser console for any JavaScript errors
