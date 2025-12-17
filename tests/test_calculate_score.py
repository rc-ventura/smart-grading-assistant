"""Unit tests for calculate_final_score tool.

These tests validate the state-based contract expected by calculate_final_score
and ensure score aggregation and approval thresholds behave as designed.

The tool now reads grades from session state instead of JSON input.
"""

import os
import sys

# Add parent directory to path for imports (similar to test_guardrail_scenarios)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calculate_score import calculate_final_score


class MockState(dict):
    """Mock state object that behaves like ADK session state."""
    def get(self, key, default=None):
        return super().get(key, default)


class MockToolContext:
    """Mock ToolContext for testing."""
    def __init__(self, state_data: dict = None):
        self.state = MockState(state_data or {})


def test_calculate_final_score_happy_path():
    """Grades in state should yield correct totals and letter grade."""
    state = {
        "grader_output_keys": ["grade_clarity", "grade_content"],
        "grade_clarity": {
            "criterion_name": "Clarity",
            "score": 20,
            "max_score": 25,
            "evaluation_notes": "Good"
        },
        "grade_content": {
            "criterion_name": "Content",
            "score": 30,
            "max_score": 35,
            "evaluation_notes": "Very good"
        },
    }
    ctx = MockToolContext(state)
    result = calculate_final_score(ctx)

    assert result["status"] == "success"
    # Totals: 20 + 30 = 50; max: 25 + 35 = 60
    assert result["total_score"] == 50
    assert result["max_possible"] == 60
    assert result["percentage"] == round(50 / 60 * 100, 1)
    assert "letter_grade" in result
    assert isinstance(result["grade_details"], list)
    assert len(result["grade_details"]) == 2


def test_calculate_final_score_missing_grader_keys():
    """Missing grader_output_keys should return an error status."""
    ctx = MockToolContext({})
    result = calculate_final_score(ctx)

    assert result["status"] == "error"
    assert "grader_output_keys" in result["error_message"].lower() or "graders" in result["error_message"].lower()


def test_calculate_final_score_missing_grade_data():
    """Missing grade data for a key should be reported."""
    state = {
        "grader_output_keys": ["grade_clarity", "grade_content"],
        "grade_clarity": {
            "criterion_name": "Clarity",
            "score": 20,
            "max_score": 25,
            "evaluation_notes": "Good"
        },
        # grade_content is missing
    }
    ctx = MockToolContext(state)
    result = calculate_final_score(ctx)

    # Should still succeed with partial grades (1 out of 2)
    assert result["status"] == "success"
    assert result["total_score"] == 20
    assert result["max_possible"] == 25


def test_calculate_final_score_clamps_score_bounds():
    """Scores below 0 or above max_score should be clamped into [0, max_score]."""
    state = {
        "grader_output_keys": ["grade_low", "grade_high"],
        "grade_low": {
            "criterion_name": "Low",
            "score": -5,
            "max_score": 10,
            "evaluation_notes": "Too low"
        },
        "grade_high": {
            "criterion_name": "High",
            "score": 20,
            "max_score": 15,
            "evaluation_notes": "Too high"
        },
    }
    ctx = MockToolContext(state)
    result = calculate_final_score(ctx)

    assert result["status"] == "success"
    # Clamped scores: 0 and 15 => total 15, max 25
    assert result["total_score"] == 15
    assert result["max_possible"] == 25


def test_calculate_final_score_requires_approval_thresholds():
    """Ensure approval flags toggle correctly for low/high percentages."""
    # Case 1: failing (<50%)
    low_state = {
        "grader_output_keys": ["grade_any"],
        "grade_any": {"criterion_name": "Any", "score": 10, "max_score": 30, "evaluation_notes": "Low"}
    }
    low_ctx = MockToolContext(low_state)
    low_result = calculate_final_score(low_ctx)

    assert low_result["requires_human_approval"] is True
    assert "below passing threshold" in low_result["approval_reason"]

    # Case 2: exceptional (>90%)
    high_state = {
        "grader_output_keys": ["grade_any"],
        "grade_any": {"criterion_name": "Any", "score": 95, "max_score": 100, "evaluation_notes": "High"}
    }
    high_ctx = MockToolContext(high_state)
    high_result = calculate_final_score(high_ctx)

    assert high_result["requires_human_approval"] is True
    assert "exceptional" in high_result["approval_reason"]


def run_all_tests():
    """Run all calculate_final_score tests and print summary."""
    print("\n" + "=" * 70)
    print("📊 CALCULATE_FINAL_SCORE - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Happy path", test_calculate_final_score_happy_path),
        ("Missing grader keys", test_calculate_final_score_missing_grader_keys),
        ("Missing grade data", test_calculate_final_score_missing_grade_data),
        ("Clamp score bounds", test_calculate_final_score_clamps_score_bounds),
        ("Approval thresholds", test_calculate_final_score_requires_approval_thresholds),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in tests:
        print("\n" + "-" * 70)
        print(f"🧪 TEST: {name}")
        print("-" * 70)
        try:
            if test_fn() is None or test_fn():
                passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((name, f"AssertionError: {e}"))
            print(f"   ❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))
            print(f"   ❌ ERROR: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY - calculate_final_score")
    print("=" * 70)
    print(f"   Total tests: {len(tests)}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")

    if errors:
        print("\n   Failures:")
        for name, error in errors:
            print(f"     - {name}: {error}")

    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
