"""Rubric Validator Agent - validates rubric structure before grading."""

from google.adk.agents import LlmAgent

from services.llm_provider import get_model, get_agent_generate_config
from config import MODEL_LITE, retry_config
from tools.validate_rubric import validate_rubric


def create_rubric_validator_agent(model=None):
    """Factory function to create a RubricValidatorAgent with optional model."""
    if model is None:
        model = get_model()
    
    return LlmAgent(
        name="RubricValidatorAgent",
        model=model,
        generate_content_config=get_agent_generate_config(),
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


# Default singleton instance (backward compatibility)
rubric_validator_agent = create_rubric_validator_agent()

print("✅ RubricValidatorAgent created")
