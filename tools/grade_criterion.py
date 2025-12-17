"""
Grade Criterion Tool

This tool grades a submission against a single criterion from the rubric.
Used by the parallel grading agents to evaluate different aspects simultaneously.

Concept from course: Day 2 - Custom Tools (FunctionTool)
"""

from typing import Any


def grade_criterion(
    criterion_name: str,
    criterion_description: str,
    max_score: int,
    score: float,
    submission_content: str,
    evaluation_notes: str
) -> dict:
    """Records the grade for a single criterion based on agent's evaluation.
    
    This tool is called by the grading agent after it has analyzed the submission
    against a specific criterion. The agent provides its evaluation notes and
    the score it determined.
    
    Args:
        criterion_name: Name of the criterion being evaluated (e.g., "Code Quality")
        criterion_description: Description of what this criterion evaluates
        max_score: Maximum possible score for this criterion
        submission_content: The student's submission text/code being evaluated
        evaluation_notes: The agent's detailed evaluation notes and justification
    
    Returns:
        Dictionary with the grading result:
        {
            "criterion": "Code Quality",
            "max_score": 30,
            "status": "graded",
            "evaluation_notes": "...",
            "message": "Criterion 'Code Quality' has been evaluated"
        }
    
    Note: The actual score is determined by the agent based on the evaluation
          and passed as the `score` argument. This tool validates and records
          the evaluation metadata for the aggregator.
    """
    
    # Validate inputs
    if not criterion_name or not criterion_name.strip():
        return {
            "status": "error",
            "error_message": "Criterion name cannot be empty"
        }
    
    if max_score <= 0:
        return {
            "status": "error", 
            "error_message": "Max score must be positive"
        }
    
    # Validate numeric score
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "error_message": "Score must be a number"
        }

    # Clamp score to valid range [0, max_score]
    if numeric_score < 0:
        numeric_score = 0
    if numeric_score > max_score:
        numeric_score = max_score
    
    if not submission_content or not submission_content.strip():
        return {
            "status": "error",
            "error_message": "Submission content cannot be empty"
        }
    
    if not evaluation_notes or not evaluation_notes.strip():
        return {
            "status": "error",
            "error_message": "Evaluation notes cannot be empty - provide justification"
        }
    
    # Return structured result for the aggregator
    return {
        "status": "graded",
        "criterion": criterion_name,
        "criterion_description": criterion_description,
        "max_score": max_score,
        "score": numeric_score,
        "evaluation_notes": evaluation_notes,
        "submission_preview": submission_content[:200] + "..." if len(submission_content) > 200 else submission_content,
        "message": f"Criterion '{criterion_name}' (max {max_score} pts) has been evaluated"
    }
