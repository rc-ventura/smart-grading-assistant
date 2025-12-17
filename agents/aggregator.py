"""Aggregator Agent - combines criterion grades into final score."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from config import MODEL_LITE, retry_config
from tools.build_grades_payload import build_grades_payload
from tools.calculate_score import calculate_final_score


aggregator_agent = LlmAgent(
    name="AggregatorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Aggregates individual criterion grades into a final score",
    instruction="""You are a grade aggregator. You MUST complete these steps IN ORDER:
    
    STEP 1: Call build_grades_payload tool (no parameters needed).
            This returns a JSON payload with all criterion grades.
    
    STEP 2: Call calculate_final_score tool using the grades_json value from Step 1.
            This computes the final score, percentage, letter grade, and approval status.
    
    STEP 3: After BOTH tools are called, briefly summarize:
            - Final score and letter grade
            - Whether human approval is required
    
    DO NOT skip Step 2. You MUST call both tools in sequence.
    The workflow is incomplete if you only call build_grades_payload.""",
    tools=[build_grades_payload, calculate_final_score],
    output_key="aggregation_result",
)

print("✅ AggregatorAgent created")
