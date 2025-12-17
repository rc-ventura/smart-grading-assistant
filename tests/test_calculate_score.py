"""Unit tests for calculate_final_score tool.

These tests validate the JSON contract expected by calculate_final_score
and ensure score aggregation and approval thresholds behave as designed.
"""

import json
import os
import sys

# Add parent directory to path for imports (similar to test_guardrail_scenarios)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calculate_score import calculate_final_score


def test_calculate_final_score_happy_path():
    """Grades JSON with multiple criteria should yield correct totals and letter grade."""
    payload = {
        "grades": [
            {"criterion": "Clarity", "score": 20, "max_score": 25, "justification": "Good"},
            {"criterion": "Content", "score": 30, "max_score": 35, "justification": "Very good"},
        ]
    }
    result = calculate_final_score(json.dumps(payload))

    assert result["status"] == "success"
    # Totals: 20 + 30 = 50; max: 25 + 35 = 60
    assert result["total_score"] == 50
    assert result["max_possible"] == 60
    assert result["percentage"] == round(50 / 60 * 100, 1)
    assert "letter_grade" in result
    assert isinstance(result["grade_details"], list)
    assert len(result["grade_details"]) == 2


def test_calculate_final_score_missing_grades_field():
    """Missing 'grades' field should return an error status."""
    payload = {"foo": []}
    result = calculate_final_score(json.dumps(payload))

    assert result["status"] == "error"
    assert "Missing 'grades' field" in result["error_message"]


def test_calculate_final_score_empty_grades_list():
    """Empty 'grades' list should be rejected."""
    payload = {"grades": []}
    result = calculate_final_score(json.dumps(payload))

    assert result["status"] == "error"
    assert "must be a non-empty list" in result["error_message"]


def test_calculate_final_score_missing_score_or_max_score():
    """Each grade must include both score and max_score fields."""
    payload = {
        "grades": [
            {"criterion": "Clarity", "score": 10},  # missing max_score
        ]
    }
    result = calculate_final_score(json.dumps(payload))

    assert result["status"] == "error"
    assert "Each grade must have 'score' and 'max_score'" in result["error_message"]


def test_calculate_final_score_clamps_score_bounds():
    """Scores below 0 or above max_score should be clamped into [0, max_score]."""
    payload = {
        "grades": [
            {"criterion": "Low", "score": -5, "max_score": 10, "justification": "Too low"},
            {"criterion": "High", "score": 20, "max_score": 15, "justification": "Too high"},
        ]
    }
    result = calculate_final_score(json.dumps(payload))

    assert result["status"] == "success"
    # Clamped scores: 0 and 15 => total 15, max 25
    assert result["total_score"] == 15
    assert result["max_possible"] == 25


def test_calculate_final_score_requires_approval_thresholds():
    """Ensure approval flags toggle correctly for low/high percentages."""
    # Case 1: failing (<50%)
    low_payload = {"grades": [{"criterion": "Any", "score": 10, "max_score": 30, "justification": "Low"}]}
    low_result = calculate_final_score(json.dumps(low_payload))

    assert low_result["requires_human_approval"] is True
    assert "below passing threshold" in low_result["approval_reason"]

    # Case 2: exceptional (>90%)
    high_payload = {"grades": [{"criterion": "Any", "score": 95, "max_score": 100, "justification": "High"}]}
    high_result = calculate_final_score(json.dumps(high_payload))

    assert high_result["requires_human_approval"] is True
    assert "exceptional" in high_result["approval_reason"]


def run_all_tests():
    """Run all calculate_final_score tests and print summary."""
    print("\n" + "=" * 70)
    print("📊 CALCULATE_FINAL_SCORE - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Happy path", test_calculate_final_score_happy_path),
        ("Missing 'grades' field", test_calculate_final_score_missing_grades_field),
        ("Empty 'grades' list", test_calculate_final_score_empty_grades_list),
        ("Missing score/max_score", test_calculate_final_score_missing_score_or_max_score),
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
