"""Aggregator Agent - combines criterion grades into final score."""

from google.adk.agents import LlmAgent

from services.llm_provider import get_model, get_agent_generate_config
from models.schemas import AggregationResult
from tools.calculate_score import calculate_final_score


aggregator_agent = LlmAgent(
    name="AggregatorAgent",
    model=get_model(),
    generate_content_config=get_agent_generate_config(),
    description="Aggregates individual criterion grades into a final score",
    instruction="""You are a grade aggregator. Your job is to calculate the final score.

STEP 1: Call calculate_final_score with the grades from session state.
        The grader_output_keys in state tells you which keys have grades.
        Each grade key (e.g., grade_code_quality) contains a CriterionGrade with:
        - criterion_name, max_score, score, evaluation_notes

STEP 2: Return the aggregation result as structured JSON.

The calculate_final_score tool will:
- Sum all scores and max_scores
- Calculate percentage and letter grade
- Determine if human approval is needed (< 50% or > 90%)

Return the final result in the required JSON format.""",
    tools=[calculate_final_score],
    output_schema=AggregationResult,
    output_key="aggregation_result",
)

print("✅ AggregatorAgent created")
