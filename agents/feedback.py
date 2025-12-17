"""Feedback Generator Agent - creates constructive feedback for students."""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from config import MODEL_LITE, retry_config


feedback_agent = LlmAgent(
    name="FeedbackGeneratorAgent",
    model=Gemini(model=MODEL_LITE, retry_options=retry_config),
    description="Generates comprehensive feedback for the student",
    instruction="""You are a feedback specialist. Your job is to create 
    constructive, encouraging feedback for the student.
    
    Based on all the evaluation data in the session state:
    1. Start with positive aspects (what the student did well)
    2. Identify specific areas for improvement
    3. Provide actionable suggestions
    4. End with encouragement
    
    Your feedback should be:
    - Specific (reference actual parts of the submission)
    - Constructive (focus on improvement, not criticism)
    - Encouraging (motivate continued learning)
    - Clear (easy for the student to understand)
    
    Format your feedback in a clear, readable structure.""",
    output_key="final_feedback",
)

print("✅ FeedbackGeneratorAgent created")
