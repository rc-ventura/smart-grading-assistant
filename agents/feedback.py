"""Feedback Generator Agent - creates constructive feedback for students."""

from google.adk.agents import LlmAgent

from services.gemini_client import get_model, get_agent_generate_config
from config import MODEL_LITE, retry_config
from models.schemas import FinalFeedback


feedback_agent = LlmAgent(
    name="FeedbackGeneratorAgent",
    model=get_model(),
    generate_content_config=get_agent_generate_config(),
    description="Generates comprehensive feedback for the student",
    instruction="""You are a feedback specialist. Your job is to create 
constructive, encouraging feedback for the student.

Based on all the evaluation data in the session state (aggregation_result, grade details):
1. Identify strengths (what the student did well)
2. Identify specific areas for improvement
3. Provide actionable suggestions
4. Write an encouraging closing message
5. Write a brief overall summary

Your feedback should be:
- Specific (reference actual parts of the submission)
- Constructive (focus on improvement, not criticism)
- Encouraging (motivate continued learning)
- Clear (easy for the student to understand)

Return your feedback as structured JSON with the required fields.""",
    output_schema=FinalFeedback,
    output_key="final_feedback",
)

print("✅ FeedbackGeneratorAgent created")
