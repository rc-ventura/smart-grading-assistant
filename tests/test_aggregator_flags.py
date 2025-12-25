
import pytest
from unittest.mock import MagicMock
from tools.calculate_score import calculate_final_score
from config.settings import FAILING_THRESHOLD, EXCEPTIONAL_THRESHOLD

class MockToolContext:
    def __init__(self, state):
        self.state = state

def test_aggregator_flags_normal_score():
    """Test that a normal score (e.g., 75%) does NOT trigger intervention."""
    state = {
        "grader_output_keys": ["grade_test"],
        "grade_test": {
            "criterion_name": "Test Criterion",
            "score": 75,
            "max_score": 100,
            "evaluation_notes": "Normal"
        }
    }
    context = MockToolContext(state)
    result = calculate_final_score(context)
    
    assert result["percentage"] == 75.0
    assert result["requires_human_intervention"] is False
    assert result["anomaly_reason"] is None

def test_aggregator_flags_failing_score():
    """Test that a failing score (e.g., < FAILING_THRESHOLD) triggers intervention."""
    # Ensure we use a score strictly below the threshold
    failing_score = FAILING_THRESHOLD - 10
    
    state = {
        "grader_output_keys": ["grade_test"],
        "grade_test": {
            "criterion_name": "Test Criterion",
            "score": failing_score,
            "max_score": 100,
            "evaluation_notes": "Failing"
        }
    }
    context = MockToolContext(state)
    result = calculate_final_score(context)
    
    assert result["percentage"] == float(failing_score)
    assert result["requires_human_intervention"] is True
    assert "below passing threshold" in result["anomaly_reason"]

def test_aggregator_flags_exceptional_score():
    """Test that an exceptional score (e.g., > EXCEPTIONAL_THRESHOLD) triggers intervention."""
    # Ensure we use a score strictly above the threshold
    exceptional_score = EXCEPTIONAL_THRESHOLD + 5
    if exceptional_score > 100:
        exceptional_score = 100 # Cap at 100 if threshold is high, but usually threshold is 80-90
        
    state = {
        "grader_output_keys": ["grade_test"],
        "grade_test": {
            "criterion_name": "Test Criterion",
            "score": exceptional_score,
            "max_score": 100,
            "evaluation_notes": "Exceptional"
        }
    }
    context = MockToolContext(state)
    result = calculate_final_score(context)
    
    assert result["percentage"] == float(exceptional_score)
    assert result["requires_human_intervention"] is True
    assert "is exceptional" in result["anomaly_reason"]

def test_aggregator_flags_missing_grades():
    """Test that missing grades trigger intervention."""
    state = {
        "grader_output_keys": ["grade_test"],
        # grade_test is missing from state
    }
    context = MockToolContext(state)
    result = calculate_final_score(context)
    
    assert result["requires_human_intervention"] is True
    assert "missing valid grades" in result["anomaly_reason"]

def test_aggregator_flags_failed_grades():
    """Test that failed grades (errors) trigger intervention."""
    state = {
        "grader_output_keys": ["grade_test"],
        "grade_test_error": {
            "error_message": "LLM Failure"
        }
    }
    context = MockToolContext(state)
    result = calculate_final_score(context)
    
    assert result["requires_human_intervention"] is True
    assert "One or more criteria failed to grade" in result["anomaly_reason"]
