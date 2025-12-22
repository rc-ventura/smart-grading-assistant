"""Approval Agent - handles human-in-the-loop for edge case grades."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from services.llm_provider import get_model, get_agent_generate_config
from tools.finalize_grade import finalize_grade, needs_approval


def create_approval_agent(model=None):
    """Factory function to create an ApprovalAgent with optional model."""
    if model is None:
        model = get_model()
    
    return LlmAgent(
        name="ApprovalAgent",
        model=model,
        generate_content_config=get_agent_generate_config(),
        description="Handles human approval for edge case grades",
        instruction="""You finalize grades. 
        
        Read the aggregation_result from session state (saved by AggregatorAgent).
        Call finalize_grade ONCE with the values from aggregation_result.
        
        The system will automatically request human confirmation if the grade is an edge case.
        After calling finalize_grade, do NOT generate additional text.""",
        tools=[FunctionTool(finalize_grade, require_confirmation=needs_approval)],
        output_key="approval_result",
    )


# Default singleton instance (backward compatibility)
approval_agent = create_approval_agent()

print("✅ ApprovalAgent created")
