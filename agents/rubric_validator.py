"""Rubric Validator Agent - validates rubric structure before grading."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from config import MODEL_LITE, retry_config
from tools.validate_rubric import validate_rubric


rubric_validator_agent = LlmAgent(
    name="RubricValidatorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Validates the structure and completeness of grading rubrics",
    instruction="""You are a rubric validation specialist. Your job is to validate 
    grading rubrics before they are used for evaluation.

    When you receive a rubric:
    1. Use the validate_rubric tool to check its structure.
    2. If valid, clearly confirm that the rubric is ready and list the criteria in a friendly way.
    3. If invalid, provide user-friendly error handling:
       - Start with a short, clear message that the rubric is not ready for grading.
       - List the specific problems in a structured way (bulleted list or numbered list).
       - For each problem, explain exactly what the teacher needs to change in the rubric.
       - End by saying explicitly that grading will NOT proceed until the rubric is fixed and validated again.

    Your tone should be professional, clear, and encouraging. Assume the user is a teacher who may not be technical.
    Always be precise and helpful in your feedback.""",
    tools=[validate_rubric],
    output_key="validation_result",
)

print("✅ RubricValidatorAgent created")
