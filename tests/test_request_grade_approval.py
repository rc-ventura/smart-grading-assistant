"""Unit tests for the finalize_grade tool and needs_approval function.

These tests verify:
1. finalize_grade returns correct structure
2. needs_approval returns True for scores < 50% or > 90%
3. needs_approval returns False for scores between 50% and 90%
"""

import asyncio

from capstone.agents.approval import finalize_grade, needs_approval


class MockToolContext:
    """Mock ToolContext for testing needs_approval."""
    pass


def test_finalize_grade_returns_correct_structure():
    """finalize_grade should return a dict with all grade info."""

    result = finalize_grade(
        final_score=40,
        max_score=100,
        percentage=40.0,
        letter_grade="F",
        reason="Score below threshold",
    )

    assert result["status"] == "finalized"
    assert result["final_score"] == 40
    assert result["max_score"] == 100
    assert result["percentage"] == 40.0
    assert result["letter_grade"] == "F"
    assert "finalized" in result["message"]


def test_needs_approval_low_score():
    """needs_approval should return True for scores < 50%."""
    ctx = MockToolContext()
    
    result = asyncio.run(needs_approval(
        final_score=40,
        max_score=100,
        percentage=40.0,
        letter_grade="F",
        reason="Low score",
    ))
    
    assert result is True


def test_needs_approval_high_score():
    """needs_approval should return True for scores > 90%."""
    ctx = MockToolContext()
    
    result = asyncio.run(needs_approval(
        final_score=95,
        max_score=100,
        percentage=95.0,
        letter_grade="A",
        reason="Exceptional score",
    ))
    
    assert result is True


def test_needs_approval_normal_score():
    """needs_approval should return False for scores between 50% and 90%."""
    ctx = MockToolContext()
    
    result = asyncio.run(needs_approval(
        final_score=75,
        max_score=100,
        percentage=75.0,
        letter_grade="C",
        reason="Normal score",
    ))
    
    assert result is False


def run_all_tests():
    """Run all finalize_grade and needs_approval tests and print summary."""

    print("\n" + "=" * 70)
    print("📊 FINALIZE_GRADE & NEEDS_APPROVAL - TEST SUITE")
    print("=" * 70)

    tests = [
        ("finalize_grade structure", test_finalize_grade_returns_correct_structure),
        ("needs_approval low score", test_needs_approval_low_score),
        ("needs_approval high score", test_needs_approval_high_score),
        ("needs_approval normal score", test_needs_approval_normal_score),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in tests:
        print("\n" + "-" * 70)
        print(f"🧪 TEST: {name}")
        print("-" * 70)
        try:
            test_fn()
            passed += 1
            print(f"   ✅ PASS")
        except AssertionError as e:
            failed += 1
            errors.append((name, f"AssertionError: {e}"))
            print(f"   ❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))
            print(f"   ❌ ERROR: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY - finalize_grade & needs_approval")
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
