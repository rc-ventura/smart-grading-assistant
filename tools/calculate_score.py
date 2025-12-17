"""
Calculate Final Score Tool

This tool calculates the final score from individual criterion grades
stored in session state. It reads the structured outputs from graders
and aggregates them.

Concept from course: Day 2 - Custom Tools (FunctionTool)
"""

import json
from typing import Any, Dict, List, Optional

from google.adk.tools.tool_context import ToolContext


def calculate_final_score(tool_context: ToolContext) -> dict:
    """Calculates the final score from criterion grades in session state.
    
    This tool reads grades directly from session state (populated by graders
    using output_schema) and aggregates them into a final score.
    
    The graders store their results in state keys like "grade_code_quality"
    with CriterionGrade schema: {criterion_name, max_score, score, evaluation_notes}
    
    Returns:
        Dictionary with final score calculation:
        {
            "status": "success",
            "total_score": 85,
            "max_possible": 100,
            "percentage": 85.0,
            "letter_grade": "B",
            "grade_details": [...],
            "requires_human_approval": True/False,
            "approval_reason": "Score below 50%" or None
        }
    """
    state = tool_context.state
    
    # Get grader output keys from state
    try:
        grader_output_keys = state.get("grader_output_keys")
    except Exception:
        grader_output_keys = None
    
    if not grader_output_keys:
        # Try to infer from rubric
        try:
            rubric = state.get("rubric")
            if rubric and isinstance(rubric, dict):
                criteria = rubric.get("criteria", [])
                grader_output_keys = [f"grade_{c.get('slug')}" for c in criteria if c.get('slug')]
        except Exception:
            pass
    
    if not grader_output_keys:
        return {
            "status": "error",
            "error_message": "No grader_output_keys found in state. Graders may not have run.",
            "recoverable": True,
            "suggestion": "Ensure parallel graders completed successfully before aggregation."
        }
    
    # Collect grades from state
    grades: List[Dict[str, Any]] = []
    errors: List[str] = []
    
    for key in grader_output_keys:
        grade_data = None
        
        # Try multiple locations where grade might be stored
        for try_key in [key, f"{key}_dict"]:
            try:
                grade_data = state.get(try_key)
                if isinstance(grade_data, dict) and "score" in grade_data:
                    break
                # Handle Pydantic model stored as dict
                if isinstance(grade_data, dict) and "criterion_name" in grade_data:
                    break
            except Exception:
                continue
        
        if not isinstance(grade_data, dict):
            errors.append(f"Missing grade data for '{key}'")
            continue
        
        # Extract score and max_score (handle both old and new schema)
        score = grade_data.get("score")
        max_score = grade_data.get("max_score")
        criterion_name = grade_data.get("criterion_name") or grade_data.get("criterion", "Unknown")
        justification = grade_data.get("evaluation_notes") or grade_data.get("justification", "")
        
        if score is None or max_score is None:
            errors.append(f"Grade '{key}' missing score or max_score")
            continue
        
        try:
            score = float(score)
            max_score = float(max_score)
        except (TypeError, ValueError):
            errors.append(f"Grade '{key}' has non-numeric score/max_score")
            continue
        
        grades.append({
            "criterion": criterion_name,
            "score": score,
            "max_score": max_score,
            "justification": justification,
        })
    
    if errors and not grades:
        return {
            "status": "error",
            "error_message": "; ".join(errors),
            "recoverable": True,
            "suggestion": "Check that all graders completed and stored their results."
        }
    
    if not grades:
        return {
            "status": "error",
            "error_message": "No valid grades found to aggregate.",
            "recoverable": True,
            "suggestion": "Ensure graders ran and stored results in session state."
        }
    
    # Calculate totals
    total_score = 0
    max_possible = 0
    grade_details = []
    
    for grade in grades:
        score = grade["score"]
        max_score = grade["max_score"]
        
        # Clamp score to valid range
        if score < 0:
            score = 0
        if score > max_score:
            score = max_score
        
        total_score += score
        max_possible += max_score
        
        grade_details.append({
            "criterion": grade["criterion"],
            "score": score,
            "max_score": max_score,
            "justification": grade["justification"],
        })
    
    # Calculate percentage
    percentage = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0
    
    # Determine letter grade
    letter_grade = _get_letter_grade(percentage)
    
    # Determine if human approval is needed
    requires_approval = False
    approval_reason = None
    
    if percentage < 50:
        requires_approval = True
        approval_reason = f"Score {percentage}% is below passing threshold (50%). Please review."
    elif percentage > 90:
        requires_approval = True
        approval_reason = f"Score {percentage}% is exceptional (>90%). Please verify accuracy."
    
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
    
    # Save to session state for downstream agents
    try:
        tool_context.state["aggregation_result"] = result
    except Exception:
        pass
    
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
