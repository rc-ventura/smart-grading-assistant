"""Feedback Generator Agent - creates constructive feedback for students."""


from google.adk.agents import LlmAgent

from services.llm_provider import get_agent_generate_config_for, get_model
from config import retry_config
from models.schemas import FinalFeedback
from models.retry_agent import RetryingAgent


def create_feedback_agent(model=None):
    """Factory function to create a FeedbackGeneratorAgent with optional model."""
    if model is None:
        model = get_model()
    
    generate_content_config = get_agent_generate_config_for("feedback")
    
    _feedback_llm = LlmAgent(
        name="FeedbackGeneratorAgent_llm",
        model=model,
        generate_content_config=generate_content_config,
        description="Generates comprehensive feedback for the student",
        instruction="""You are a feedback specialist. Your job is to create 
constructive, encouraging feedback for the student.

Based on all the evaluation data in the session state (aggregation_result, grade details):
1. Identify strengths (what the student did well)
2. Identify specific areas for improvement
3. Provide actionable suggestions
4. Write an encouraging closing message
5. Write a brief overall summary

Constraints (to keep output reliable):
- strengths: 3 items max
- areas_for_improvement: 3 items max
- suggestions: 3 items max
- each list item: max 200 characters; no newlines
- encouragement: max 300 characters; no newlines
- overall_summary: max 400 characters; no newlines

Your feedback should be:
- Specific (reference actual parts of the submission)
- Constructive (focus on improvement, not criticism)
- Encouraging (motivate continued learning)
- Clear (easy for the student to understand)

Return your feedback as structured JSON with the required fields.
Do NOT include any text outside the JSON.""",
        output_schema=FinalFeedback,
        output_key="final_feedback",
    )
    
    return RetryingAgent(
        name="FeedbackGeneratorAgent",
        description=_feedback_llm.description,
        inner_agent=_feedback_llm,
        output_key="final_feedback",
        max_attempts=max(1, int(getattr(retry_config, "attempts", 3) or 3)),
    )


# Default singleton instance (backward compatibility)
feedback_agent = create_feedback_agent()

print("✅ FeedbackGeneratorAgent created")
