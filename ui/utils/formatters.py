"""Formatting helpers for scores, letter grades, and feedback display."""

from typing import Any


def format_score(score: float, max_score: float) -> str:
    """Format a score as 'X / Y' with percentage."""
    percentage = (score / max_score * 100) if max_score > 0 else 0
    return f"{score:.1f} / {max_score:.0f} ({percentage:.0f}%)"


def format_letter_grade(percentage: float) -> str:
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


def format_percentage(score: float, max_score: float) -> str:
    """Format score as percentage string."""
    if max_score <= 0:
        return "0%"
    percentage = (score / max_score) * 100
    return f"{percentage:.1f}%"


def format_feedback(feedback: dict[str, Any] | None) -> str:
    """Format feedback dict into readable text."""
    if not feedback:
        return "No feedback available."
    
    sections = []
    
    if strengths := feedback.get("strengths"):
        sections.append("**Strengths:**")
        if isinstance(strengths, list):
            for item in strengths:
                sections.append(f"- {item}")
        else:
            sections.append(f"- {strengths}")
    
    if improvements := feedback.get("improvements"):
        sections.append("\n**Areas for Improvement:**")
        if isinstance(improvements, list):
            for item in improvements:
                sections.append(f"- {item}")
        else:
            sections.append(f"- {improvements}")
    
    if suggestions := feedback.get("suggestions"):
        sections.append("\n**Suggestions:**")
        if isinstance(suggestions, list):
            for item in suggestions:
                sections.append(f"- {item}")
        else:
            sections.append(f"- {suggestions}")
    
    if summary := feedback.get("overall_summary"):
        sections.append(f"\n**Summary:** {summary}")
    
    return "\n".join(sections) if sections else "No feedback available."


def format_criterion_grade(grade: dict[str, Any]) -> dict[str, str]:
    """Format a single criterion grade for display."""
    return {
        "Criterion": grade.get("criterion_name", "Unknown"),
        "Score": format_score(
            grade.get("score", 0),
            grade.get("max_score", 0)
        ),
        "Notes": grade.get("evaluation_notes", "No notes"),
    }
