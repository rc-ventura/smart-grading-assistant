"""Grader agents for evaluating submissions against rubric criteria."""

import logging
from typing import List, Tuple

from google.adk.agents import LlmAgent, ParallelAgent

from services.gemini_client import get_model, get_agent_generate_config
from models.schemas import CriterionGrade
from utils.text_utils import slugify


def create_criterion_grader(criterion_name: str, criterion_description: str, max_score: int) -> LlmAgent:
    """Factory function to create a grader agent for a specific criterion.
    
    Uses output_schema to FORCE structured JSON output, preventing the LLM
    from returning plain text that breaks the aggregator.
    """
    criterion_slug = slugify(criterion_name)
    return LlmAgent(
        name=f"Grader_{criterion_slug}",
        model=get_model(),
        generate_content_config=get_agent_generate_config(),
        description=f"Evaluates submissions for: {criterion_name}",
        instruction=f"""You are an expert evaluator for the criterion: "{criterion_name}"
        
Criterion Description: {criterion_description}
Maximum Score: {max_score} points

IMPORTANT: The student submission is available in session state as "submission_text".
Look for the code/text that was submitted by the student.

Your task:
1. Find and read the student's submission from the conversation or state
2. Evaluate it against this specific criterion: {criterion_name}
3. Determine a score from 0 to {max_score}
4. Return your evaluation as structured JSON with these EXACT fields:
   - criterion_name: "{criterion_name}"
   - max_score: {max_score}
   - score: your determined score (number between 0 and {max_score})
   - evaluation_notes: your detailed evaluation justification

Be fair, consistent, and constructive in your evaluation notes.
Focus ONLY on this criterion. Do NOT include any text outside the JSON structure.""",
        output_schema=CriterionGrade,
        output_key=f"grade_{criterion_slug}",
    )


def build_graders_from_rubric(rubric: dict) -> Tuple[List[LlmAgent], List[str]]:
    """Build grader agents and their output keys from rubric criteria."""
    graders: List[LlmAgent] = []
    grade_keys: List[str] = []
    criteria = rubric.get("criteria") or []
    for criterion in criteria:
        name = criterion.get("name") or "Unnamed Criterion"
        desc = criterion.get("description") or "No description provided"
        max_score = criterion.get("max_score") or 0
        slug = criterion.get("slug") or slugify(name)
        try:
            graders.append(create_criterion_grader(name, desc, max_score))
            grade_keys.append(f"grade_{slug}")
        except Exception as exc:
            logging.warning("Failed to create grader for criterion '%s': %s", name, exc)
    return graders, grade_keys


# Default graders for Python code rubric (will be replaced dynamically when rubric is provided)
code_quality_grader = create_criterion_grader(
    "Code Quality", 
    "Evaluate code readability, naming conventions, and PEP 8 adherence",
    30
)

functionality_grader = create_criterion_grader(
    "Functionality",
    "Evaluate if the code correctly solves the problem",
    40
)

documentation_grader = create_criterion_grader(
    "Documentation",
    "Evaluate docstrings, comments, and code explanation",
    30
)

DEFAULT_GRADE_OUTPUT_KEYS = [
    code_quality_grader.output_key,
    functionality_grader.output_key,
    documentation_grader.output_key,
]

# Grading agent group (parallel execution for efficiency)
parallel_graders = ParallelAgent(
    name="ParallelGraders",  # Name expected by guardrail
    sub_agents=[code_quality_grader, functionality_grader, documentation_grader],
)

print("✅ Graders module loaded (3 default criterion graders, parallel mode)")
