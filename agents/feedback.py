"""Feedback Generator Agent - creates constructive feedback for students."""

import asyncio
from typing import Optional

from pydantic import ValidationError

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.utils.context_utils import Aclosing

from services.llm_provider import get_agent_generate_config_for, get_model
from config import retry_config
from models.schemas import FinalFeedback


class EmptyFeedbackOutputError(RuntimeError):
    pass


#Wrapper agent to retry feedback generation
class RetryingFeedbackAgent(BaseAgent):
    inner_agent: LlmAgent
    output_key: str
    max_attempts: int = 3

# Delegate all attributes to inner agent
    def __getattr__(self, item: str):
        try:
            return super().__getattr__(item)
        except AttributeError:
            inner_agent = object.__getattribute__(self, "inner_agent")
            if hasattr(inner_agent, item):
                return getattr(inner_agent, item)
            raise

    async def _run_async_impl(self, ctx: InvocationContext):
        last_error: Optional[Exception] = None
        last_error_type: str = "validation"
        for attempt in range(1, self.max_attempts + 1):
            try:
                ctx.end_of_agents.pop(self.inner_agent.name, None)
            except Exception:
                pass

            saw_output = False
            try:
                async with Aclosing(self.inner_agent.run_async(ctx)) as agen:
                    async for event in agen:
                        try:
                            state_delta = getattr(
                                getattr(event, "actions", None), "state_delta", None
                            )
                            if isinstance(state_delta, dict) and self.output_key in state_delta:
                                if state_delta.get(self.output_key) is not None:
                                    saw_output = True
                        except Exception:
                            pass
                        yield event

                if not saw_output:
                    raise EmptyFeedbackOutputError(
                        f"Empty or missing output for key '{self.output_key}'"
                    )
                return
            except (ValidationError, EmptyFeedbackOutputError) as exc:
                last_error = exc
                if isinstance(exc, EmptyFeedbackOutputError):
                    last_error_type = "empty_output"
                else:
                    last_error_type = "validation"

                if attempt >= self.max_attempts:
                    break

                initial_delay = float(getattr(retry_config, "initial_delay", 1.0) or 1.0)
                exp_base = float(getattr(retry_config, "exp_base", 2.0) or 2.0)
                delay = min(10.0, initial_delay * (exp_base ** (attempt - 1)))
                await asyncio.sleep(delay)

        error_payload = {
            "error_type": last_error_type,
            "error_message": str(last_error) if last_error else "Unknown validation error",
            "recoverable": True,
            "suggestion": "Retry feedback generation.",
            "attempts": self.max_attempts,
        }

        error_key = f"{self.output_key}_error"
        event = Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
        )
        event.actions.state_delta[error_key] = error_payload
        yield event


generate_content_config = get_agent_generate_config_for("feedback")

_feedback_llm = LlmAgent(
    name="FeedbackGeneratorAgent_llm",
    model=get_model(),
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

feedback_agent = RetryingFeedbackAgent(
    name="FeedbackGeneratorAgent",
    description=_feedback_llm.description,
    inner_agent=_feedback_llm,
    output_key="final_feedback",
    max_attempts=max(1, int(getattr(retry_config, "attempts", 3) or 3)),
)

print("✅ FeedbackGeneratorAgent created")
