"""Grading validation - rubric and submission validation."""

import json
from typing import Any

import streamlit as st


def send_rubric(rubric_json: str) -> dict[str, Any]:
    """Send rubric to backend for validation.
    
    Args:
        rubric_json: JSON string containing the rubric
        
    Returns:
        Validation result dict with 'valid', 'errors', and 'criteria_count'
    """
    try:
        rubric = json.loads(rubric_json)
        
        # Basic validation (mirrors backend RubricValidatorAgent logic)
        errors = []
        
        if not isinstance(rubric, dict):
            errors.append("Rubric must be a JSON object")
        else:
            if "name" not in rubric:
                errors.append("Missing required field: 'name'")
            
            criteria = rubric.get("criteria", [])
            if not criteria:
                errors.append("Missing or empty 'criteria' array")
            else:
                total_points = 0
                for i, c in enumerate(criteria):
                    if "name" not in c:
                        errors.append(f"Criterion {i+1} missing 'name'")
                    if "max_score" not in c:
                        errors.append(f"Criterion {i+1} missing 'max_score'")
                    elif c.get("max_score", 0) <= 0:
                        errors.append(f"Criterion {i+1} 'max_score' must be positive")
                    else:
                        total_points += c.get("max_score", 0)
                    if "description" not in c:
                        errors.append(f"Criterion {i+1} missing 'description'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "criteria_count": len(rubric.get("criteria", [])),
            "total_points": total_points if not errors else 0,
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON: {str(e)}"],
            "criteria_count": 0,
            "total_points": 0,
        }


def send_submission(submission_text: str) -> dict[str, Any]:
    """Store submission in session state for grading.
    
    Args:
        submission_text: The student submission text
        
    Returns:
        Confirmation dict with 'stored', 'length', and 'preview'
    """
    if not submission_text or not submission_text.strip():
        return {
            "stored": False,
            "error": "Submission cannot be empty",
            "length": 0,
            "preview": "",
        }
    
    st.session_state.submission_text = submission_text
    
    return {
        "stored": True,
        "length": len(submission_text),
        "preview": submission_text[:200] + "..." if len(submission_text) > 200 else submission_text,
    }
