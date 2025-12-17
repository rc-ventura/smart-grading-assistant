"""
Calculate Final Score Tool

This tool calculates the final score from individual criterion grades
and determines if human approval is needed.

Concept from course: Day 2 - Custom Tools (FunctionTool)
"""

import json
from typing import Any, Optional

try:
    from google.adk.tools.tool_context import ToolContext
except ImportError:
    ToolContext = None


def calculate_final_score(grades_json: str, tool_context: Optional[Any] = None) -> dict:
    """Calculates the final score from individual criterion grades.
    
    This tool aggregates all criterion scores, calculates the final grade,
    and determines if human approval is required based on thresholds.
    
    Args:
        grades_json: JSON string with grades for each criterion.
                    Expected format:
                    {
                        "grades": [
                            {
                                "criterion": "Code Quality",
                                "score": 25,
                                "max_score": 30,
                                "justification": "Clean code with good naming..."
                            }
                        ]
                    }
    
    Returns:
        Dictionary with final score calculation:
        {
            "status": "success",
            "total_score": 85,
            "max_possible": 100,
            "percentage": 85.0,
            "letter_grade": "B",
            "requires_human_approval": True/False,
            "approval_reason": "Score below 50%" or None
        }
    """
    
    # Parse JSON
    try:
        data = json.loads(grades_json)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error_message": f"Invalid JSON format: {str(e)}"
        }
    
    # Validate structure
    if "grades" not in data:
        return {
            "status": "error",
            "error_message": "Missing 'grades' field"
        }
    
    if not isinstance(data["grades"], list) or len(data["grades"]) == 0:
        return {
            "status": "error",
            "error_message": "'grades' must be a non-empty list"
        }
    
    # Calculate totals
    total_score = 0
    max_possible = 0
    grade_details = []
    
    for grade in data["grades"]:
        if "score" not in grade or "max_score" not in grade:
            return {
                "status": "error",
                "error_message": f"Each grade must have 'score' and 'max_score' fields"
            }
        
        score = grade["score"]
        max_score = grade["max_score"]
        
        # Validate score is within bounds
        if score < 0:
            score = 0
        if score > max_score:
            score = max_score
        
        total_score += score
        max_possible += max_score
        
        grade_details.append({
            "criterion": grade.get("criterion", "Unknown"),
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 1) if max_score > 0 else 0
        })
    
    # Calculate percentage
    percentage = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0
    
    # Determine letter grade
    letter_grade = _get_letter_grade(percentage)
    
    # Determine if human approval is needed
    # Thresholds: score < 50% (failing) or score > 90% (exceptional)
    requires_approval = False
    approval_reason = None
    
    if percentage < 50:
        requires_approval = True
        approval_reason = f"Score {percentage}% is below passing threshold (50%). Please review before confirming."
    elif percentage > 90:
        requires_approval = True
        approval_reason = f"Score {percentage}% is exceptional (>90%). Please verify the evaluation is accurate."
    
    result = {
        "status": "success",
        "total_score": total_score,
        "max_possible": max_possible,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "grade_details": grade_details,
        "requires_human_approval": requires_approval,
        "approval_reason": approval_reason,
        "message": f"Final score: {total_score}/{max_possible} ({percentage}%) - Grade: {letter_grade}"
    }
    
    # Save to session state if tool_context is available
    if tool_context is not None:
        try:
            tool_context.state["aggregation_result"] = result
        except Exception:
            pass  # Best effort - don't break if state is not writable
    
    return result


def _get_letter_grade(percentage: float) -> str:
    """Convert percentage to letter grade."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"
