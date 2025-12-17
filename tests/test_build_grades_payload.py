"""Unit tests for build_grades_payload tool.

These tests validate that the tool correctly reads rubric + grade_* entries
from a mock session state and produces a grades_json payload compatible with
calculate_final_score.
"""

import json
import os
import sys

# Add parent directory to path for imports (same pattern as other tests)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.build_grades_payload import build_grades_payload
from tools.calculate_score import calculate_final_score


class MockState:
    """Minimal mock state object for testing tools."""

    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def to_dict(self):
        return self._data.copy()


class MockToolContext:
    """Mock ToolContext carrying a MockState, similar to guardrail tests."""

    def __init__(self):
        self.state = MockState()


def _build_sample_context(with_grader_output_keys: bool = True) -> MockToolContext:
    """Create a tool context with rubric + two graded criteria.

    This mirrors a realistic session after parallel graders have run.
    """

    ctx = MockToolContext()
    # Rubric with slugs, as produced by validate_rubric
    ctx.state["rubric"] = {
        "name": "Essay Evaluation Rubric",
        "criteria": [
            {
                "name": "Clarity of Argument",
                "max_score": 25,
                "description": "How clear and coherent the argument is",
                "slug": "clarity_of_argument",
            },
            {
                "name": "Use of Evidence",
                "max_score": 25,
                "description": "Quality and relevance of supporting evidence",
                "slug": "use_of_evidence",
            },
        ],
    }

    if with_grader_output_keys:
        ctx.state["grader_output_keys"] = [
            "grade_clarity_of_argument",
            "grade_use_of_evidence",
        ]

    # Grades as produced by grade_criterion (now including numeric score)
    ctx.state["grade_clarity_of_argument"] = {
        "status": "graded",
        "criterion": "Clarity of Argument",
        "criterion_description": "How clear and coherent the argument is",
        "max_score": 25,
        "score": 22,
        "evaluation_notes": "Argument is generally clear, only minor issues.",
    }

    ctx.state["grade_use_of_evidence"] = {
        "status": "graded",
        "criterion": "Use of Evidence",
        "criterion_description": "Quality and relevance of supporting evidence",
        "max_score": 25,
        "score": 18,
        "evaluation_notes": "Good evidence, but could include more diverse sources.",
    }

    return ctx


def test_build_grades_payload_happy_path_with_keys():
    """Tool should build a valid grades_json when grader_output_keys is present."""
    ctx = _build_sample_context(with_grader_output_keys=True)
    result = build_grades_payload(ctx)

    assert result["status"] == "ok"
    assert "grades_json" in result

    payload = json.loads(result["grades_json"])
    assert "grades" in payload
    grades = payload["grades"]
    assert isinstance(grades, list)
    assert len(grades) == 2

    # Check that both criteria are present with correct scores
    by_criterion = {g["criterion"]: g for g in grades}
    assert "Clarity of Argument" in by_criterion
    assert "Use of Evidence" in by_criterion

    clarity = by_criterion["Clarity of Argument"]
    evidence = by_criterion["Use of Evidence"]

    assert clarity["score"] == 22.0
    assert clarity["max_score"] == 25.0
    assert "clear" in clarity["justification"].lower()

    assert evidence["score"] == 18.0
    assert evidence["max_score"] == 25.0
    assert "evidence" in evidence["justification"].lower()

    # Sanity check: payload is accepted by calculate_final_score
    agg = calculate_final_score(result["grades_json"])
    assert agg["status"] == "success"
    assert agg["total_score"] == 40
    assert agg["max_possible"] == 50


def test_build_grades_payload_fallback_without_keys():
    """When grader_output_keys is missing, tool should infer keys from rubric slugs."""
    ctx = _build_sample_context(with_grader_output_keys=False)
    result = build_grades_payload(ctx)

    assert result["status"] == "ok"
    payload = json.loads(result["grades_json"])
    grades = payload["grades"]
    assert len(grades) == 2

    names = {g["criterion"] for g in grades}
    assert {"Clarity of Argument", "Use of Evidence"} == names


def test_build_grades_payload_error_missing_grade_data():
    """Missing grade_<slug> in state should produce an error status."""
    ctx = _build_sample_context(with_grader_output_keys=True)
    # Introduce a bad key that has no corresponding grade_ entry
    ctx.state["grader_output_keys"].append("grade_missing_criterion")

    result = build_grades_payload(ctx)

    assert result["status"] == "error"
    assert "grade_missing_criterion" in result["error_message"]


def run_all_tests():
    """Run all build_grades_payload tests and print summary."""
    print("\n" + "=" * 70)
    print("📊 BUILD_GRADES_PAYLOAD - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Happy path with explicit grader_output_keys", test_build_grades_payload_happy_path_with_keys),
        ("Fallback without grader_output_keys", test_build_grades_payload_fallback_without_keys),
        ("Error when grade data is missing", test_build_grades_payload_error_missing_grade_data),
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
    print("📊 TEST SUMMARY - build_grades_payload")
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
