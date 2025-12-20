"""
Calculate Final Score Tool

This tool calculates the final score from individual criterion grades
stored in session state. It reads the structured outputs from graders
and aggregates them.

Concept from course: Day 2 - Custom Tools (FunctionTool)
"""

import json
from typing import Any, Dict, List, Optional
from config.settings import FAILING_THRESHOLD, EXCEPTIONAL_THRESHOLD

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
    failed_criteria: List[Dict[str, Any]] = []
    missing_grade_keys: List[str] = []
    grades_by_key: Dict[str, Dict[str, Any]] = {}
    failed_by_key: Dict[str, Dict[str, Any]] = {}

    criteria_by_key: Dict[str, Dict[str, Any]] = {}
    try:
        rubric = state.get("rubric")
    except Exception:
        rubric = None

    if rubric and isinstance(rubric, dict):
        for criterion in rubric.get("criteria") or []:
            slug = criterion.get("slug")
            if not slug:
                continue
            criteria_by_key[f"grade_{slug}"] = {
                "criterion_name": criterion.get("name") or f"grade_{slug}",
                "max_score": criterion.get("max_score"),
            }
    
    for key in grader_output_keys:
        error_key = f"{key}_error"
        try:
            error_payload = state.get(error_key)
        except Exception:
            error_payload = None

        if isinstance(error_payload, dict):
            failed_criteria.append({"grade_key": key, **error_payload})
            failed_by_key[key] = error_payload
            errors.append(
                f"Grader failed for '{key}': {error_payload.get('error_message') or 'Unknown error'}"
            )
            continue

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
            missing_grade_keys.append(key)
            continue
        
        # Extract score and max_score (handle both old and new schema)
        score = grade_data.get("score")
        max_score = grade_data.get("max_score")
        criterion_name = grade_data.get("criterion_name") or grade_data.get("criterion", "Unknown")
        justification = grade_data.get("evaluation_notes") or grade_data.get("justification", "")
        
        if score is None or max_score is None:
            errors.append(f"Grade '{key}' missing score or max_score")
            missing_grade_keys.append(key)
            continue
        
        try:
            score = float(score)
            max_score = float(max_score)
        except (TypeError, ValueError):
            errors.append(f"Grade '{key}' has non-numeric score/max_score")
            missing_grade_keys.append(key)
            continue

        if max_score <= 0:
            errors.append(f"Grade '{key}' has non-positive max_score")
            missing_grade_keys.append(key)
            continue
        
        grade_entry = {
            "criterion": criterion_name,
            "score": score,
            "max_score": max_score,
            "justification": justification,
        }
        grades.append(grade_entry)
        grades_by_key[key] = grade_entry

    # Calculate totals and build grade_details (including placeholders for failures)
    total_score = 0.0
    max_possible = 0.0
    grade_details: List[Dict[str, Any]] = []

    for key in grader_output_keys:
        if key in grades_by_key:
            grade = grades_by_key[key]
            score = float(grade.get("score") or 0)
            max_score = float(grade.get("max_score") or 0)

            # Clamp score to valid range
            if score < 0:
                score = 0
            if score > max_score:
                score = max_score

            total_score += score
            max_possible += max_score
            grade_details.append(
                {
                    "criterion": grade.get("criterion") or key,
                    "score": score,
                    "max_score": max_score,
                    "justification": grade.get("justification") or "",
                }
            )
            continue

        if key in failed_by_key:
            rubric_info = criteria_by_key.get(key) or {}
            criterion_name = (
                failed_by_key[key].get("criterion_name")
                or rubric_info.get("criterion_name")
                or key
            )

            raw_max = failed_by_key[key].get("max_score")
            if raw_max is None:
                raw_max = rubric_info.get("max_score")

            try:
                max_score = float(raw_max or 0)
            except (TypeError, ValueError):
                max_score = 0.0

            if max_score > 0:
                max_possible += max_score
                grade_details.append(
                    {
                        "criterion": criterion_name,
                        "score": 0.0,
                        "max_score": max_score,
                        "justification": (
                            failed_by_key[key].get("error_message")
                            or "Failed to grade after retries."
                        ),
                    }
                )
            continue

        rubric_info = criteria_by_key.get(key) or {}
        criterion_name = rubric_info.get("criterion_name") or key
        try:
            max_score = float(rubric_info.get("max_score") or 0)
        except (TypeError, ValueError):
            max_score = 0.0

        if max_score > 0:
            max_possible += max_score
            grade_details.append(
                {
                    "criterion": criterion_name,
                    "score": 0.0,
                    "max_score": max_score,
                    "justification": "Missing grade data.",
                }
            )
    
    # Calculate percentage
    percentage = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0
    
    # Determine letter grade
    letter_grade = _get_letter_grade(percentage)
    
    # Determine if human approval is needed
    requires_approval = False
    approval_reasons: List[str] = []
    
    if failed_criteria:
        requires_approval = True
        failed_names = [
            (c.get("criterion_name") or c.get("grade_key") or "Unknown")
            for c in failed_criteria
        ]
        approval_reasons.append(
            "One or more criteria failed to grade after retries: "
            + ", ".join(failed_names)
            + ". Please review and re-run grading for those criteria."
        )

    if missing_grade_keys:
        requires_approval = True
        missing_names: List[str] = []
        for key in missing_grade_keys:
            missing_names.append((criteria_by_key.get(key) or {}).get("criterion_name") or key)
        approval_reasons.append(
            "One or more criteria are missing valid grades: "
            + ", ".join(sorted(set(missing_names)))
            + ". Please review and re-run grading for those criteria."
        )
    
    if percentage < FAILING_THRESHOLD:
        requires_approval = True
        approval_reasons.append(
            f"Score {percentage}% is below passing threshold ({FAILING_THRESHOLD}%). Please review."
        )
    elif percentage > EXCEPTIONAL_THRESHOLD:
        requires_approval = True
        approval_reasons.append(
            f"Score {percentage}% is exceptional ({EXCEPTIONAL_THRESHOLD}%). Please verify accuracy."
        )

    approval_reason = " ".join(approval_reasons) if approval_reasons else None
    
    result = {
        "status": "success",
        "total_score": total_score,
        "max_possible": max_possible,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "grade_details": grade_details,
        "requires_human_approval": requires_approval,
        "approval_reason": approval_reason,
        "message": f"Final score: {total_score}/{max_possible} ({percentage}%) - Grade: {letter_grade}",
        "failed_criteria": failed_criteria,
        "missing_grade_keys": missing_grade_keys,
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
