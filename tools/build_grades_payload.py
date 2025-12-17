"""Tool to build the grades JSON payload for calculate_final_score.

This tool reads the rubric and individual criterion grades from session
state and produces a JSON string in the exact format expected by the
calculate_final_score tool.

Concept: deterministic bridge between ParallelGraders and Aggregator.
"""

import json
from typing import Any, Dict, List

from google.adk.tools.tool_context import ToolContext


def _get_rubric_from_state(state: Any) -> Dict[str, Any]:
    """Helper to safely fetch rubric dict from state-like object."""
    try:
        rubric = state.get("rubric")
    except Exception:
        rubric = None
    return rubric or {}


def build_grades_payload(tool_context: ToolContext) -> Dict[str, Any]:
    """Build grades JSON payload for calculate_final_score from session state.

    Reads:
    - rubric: persisted by validate_rubric tool (with per-criterion slugs)
    - grader_output_keys: list of state keys like "grade_<slug>" created
      by RubricGuardrailPlugin when injecting dynamic graders.
    - grade_<slug>: result dicts produced by grade_criterion tool, each
      containing at least max_score and score fields.

    Returns:
        dict with:
        - status: "ok" or "error"
        - grades_json: JSON string in the format expected by
          calculate_final_score, when status == "ok".
        - error_message: description when status == "error".
    """
    state = tool_context.state

    rubric = _get_rubric_from_state(state)
    criteria = rubric.get("criteria") or []
    criteria_by_slug: Dict[str, Dict[str, Any]] = {}
    for c in criteria:
        slug = c.get("slug")
        if slug:
            criteria_by_slug[slug] = c

    # Discover which grade keys to use
    try:
        grader_output_keys = state.get("grader_output_keys")
    except Exception:
        grader_output_keys = None

    if not grader_output_keys:
        # Fallback: infer from rubric slugs
        if not criteria_by_slug:
            return {
                "status": "error",
                "error_message": "Cannot determine grader_output_keys: rubric or slugs missing.",
            }
        grader_output_keys = [f"grade_{slug}" for slug in criteria_by_slug.keys()]

    grades: List[Dict[str, Any]] = []
    errors: List[str] = []

    for key in grader_output_keys:
        try:
            grade_data = state.get(key)
        except Exception:
            grade_data = None

        # Primary location: state["grade_<slug>"] (if a previous version saved dicts here)
        # Fallback: state["grade_<slug>_dict"] saved by grade_criterion tool.
        if not isinstance(grade_data, dict):
            alt_key = f"{key}_dict"
            try:
                grade_data = state.get(alt_key)
            except Exception:
                grade_data = None

        if not isinstance(grade_data, dict):
            errors.append(f"Missing or invalid grade data for key '{key}'")
            continue

        # Extract slug from key: grade_<slug>
        slug = key[len("grade_"):] if key.startswith("grade_") else key
        crit = criteria_by_slug.get(slug, {})

        # Prefer score/max_score from grade_data, fall back to rubric for max_score
        score = grade_data.get("score")
        max_score = grade_data.get("max_score", crit.get("max_score"))

        if score is None or max_score is None:
            errors.append(f"Grade '{key}' is missing score or max_score")
            continue

        try:
            numeric_score = float(score)
            numeric_max = float(max_score)
        except (TypeError, ValueError):
            errors.append(f"Grade '{key}' has non-numeric score/max_score")
            continue

        criterion_name = crit.get("name") or grade_data.get("criterion", "Unknown")
        justification = grade_data.get("evaluation_notes") or grade_data.get("message", "")

        grades.append(
            {
                "criterion": criterion_name,
                "score": numeric_score,
                "max_score": numeric_max,
                "justification": justification,
            }
        )

    if errors:
        return {
            "status": "error",
            "error_message": "; ".join(errors),
        }

    if not grades:
        return {
            "status": "error",
            "error_message": "No valid grades found to build payload.",
        }

    payload = {"grades": grades}
    return {
        "status": "ok",
        "grades_json": json.dumps(payload),
    }
