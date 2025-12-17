"""
Rubric Validation Tool

This tool validates the structure and completeness of a grading rubric
before the evaluation process begins.

Concept from course: Day 2 - Custom Tools (FunctionTool)

The tool saves the validation result directly to session state so the
RubricGuardrailPlugin can check it before allowing grading agents to run.
"""

import json
from typing import Any

from google.adk.tools.tool_context import ToolContext


def validate_rubric(rubric_json: str, tool_context: ToolContext) -> dict:
    """Validates a grading rubric structure and returns validation result.
    
    This tool checks if the rubric has all required fields and proper structure
    before allowing the grading process to proceed.
    
    Args:
        rubric_json: JSON string containing the rubric with criteria.
                    Expected format:
                    {
                        "name": "Rubric Name",
                        "criteria": [
                            {
                                "name": "Criterion Name",
                                "max_score": 30,
                                "description": "What to evaluate"
                            }
                        ]
                    }
    
    Returns:
        Dictionary with validation result:
        - Success: {"status": "valid", "criteria_count": N, "total_points": M}
        - Error: {"status": "invalid", "errors": ["error1", "error2"]}
    """
    def _save_and_return(result: dict) -> dict:
        """Helper to save result to state and return it."""
        tool_context.state["rubric_validation"] = result
        return result
    
    errors = []
    
    # Parse JSON
    try:
        rubric = json.loads(rubric_json)
    except json.JSONDecodeError as e:
        return _save_and_return({
            "status": "invalid",
            "errors": [f"Invalid JSON format: {str(e)}"]
        })
    
    # Check required top-level fields
    if "name" not in rubric:
        errors.append("Missing 'name' field in rubric")
    
    if "criteria" not in rubric:
        errors.append("Missing 'criteria' field in rubric")
        return _save_and_return({"status": "invalid", "errors": errors})
    
    # Check criteria is a list
    if not isinstance(rubric["criteria"], list):
        errors.append("'criteria' must be a list")
        return _save_and_return({"status": "invalid", "errors": errors})
    
    # Check we have at least one criterion
    if len(rubric["criteria"]) == 0:
        errors.append("Rubric must have at least one criterion")
        return _save_and_return({"status": "invalid", "errors": errors})
    
    # Validate each criterion
    total_points = 0
    for i, criterion in enumerate(rubric["criteria"]):
        prefix = f"Criterion {i + 1}"
        
        if not isinstance(criterion, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        
        # Required fields for each criterion
        if "name" not in criterion:
            errors.append(f"{prefix}: missing 'name' field")
        
        if "max_score" not in criterion:
            errors.append(f"{prefix}: missing 'max_score' field")
        elif not isinstance(criterion["max_score"], (int, float)):
            errors.append(f"{prefix}: 'max_score' must be a number")
        elif criterion["max_score"] <= 0:
            errors.append(f"{prefix}: 'max_score' must be positive")
        else:
            total_points += criterion["max_score"]
        
        if "description" not in criterion:
            errors.append(f"{prefix}: missing 'description' field")
    
    # Build and return result (saves to state via helper)
    if errors:
        return _save_and_return({
            "status": "invalid",
            "errors": errors
        })
    
    # Persist the parsed rubric so downstream agents can inspect the criteria
    tool_context.state["rubric"] = rubric
    
    return _save_and_return({
        "status": "valid",
        "criteria_count": len(rubric["criteria"]),
        "total_points": total_points,
        "message": f"Rubric '{rubric['name']}' is valid with {len(rubric['criteria'])} criteria totaling {total_points} points"
    })
