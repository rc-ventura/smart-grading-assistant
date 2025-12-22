"""Generic retry wrapper agent for handling validation/output errors."""

import asyncio
from typing import Optional

from pydantic import ValidationError

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.utils.context_utils import Aclosing

from config import retry_config
from models.exceptions import EmptyOutputError


class RetryingAgent(BaseAgent):
    """Generic wrapper agent that retries inner agent on validation/empty output errors.
    
    This agent wraps an LlmAgent and automatically retries if:
    - Pydantic validation fails
    - Output is empty or missing
    
    Attributes:
        inner_agent: The LlmAgent to wrap
        output_key: Key to check for output in state_delta
        max_attempts: Maximum retry attempts (default from config)
        additional_error_info: Optional dict with extra error context
    """
    inner_agent: LlmAgent
    output_key: str
    max_attempts: int = 3
    additional_error_info: Optional[dict] = None

    def __getattr__(self, item: str):
        """Delegate attribute access to inner agent."""
        try:
            return super().__getattr__(item)
        except AttributeError:
            inner_agent = object.__getattribute__(self, "inner_agent")
            if hasattr(inner_agent, item):
                return getattr(inner_agent, item)
            raise

    async def _run_async_impl(self, ctx: InvocationContext):
        """Run inner agent with retry logic."""
        last_error: Optional[Exception] = None
        last_error_type: str = "validation"
        
        for attempt in range(1, self.max_attempts + 1):
            # Clear end_of_agents marker for retry
            try:
                ctx.end_of_agents.pop(self.inner_agent.name, None)
            except Exception:
                pass

            saw_output = False
            try:
                async with Aclosing(self.inner_agent.run_async(ctx)) as agen:
                    async for event in agen:
                        # Check if output was produced
                        try:
                            state_delta = getattr(
                                getattr(event, "actions", None), "state_delta", None
                            )
                            if isinstance(state_delta, dict) and self.output_key in state_delta:
                                output = state_delta.get(self.output_key)
                                if output is not None:
                                    # Additional validation for dict outputs
                                    if isinstance(output, dict):
                                        # Check for meaningful content
                                        if any(v for v in output.values() if v):
                                            saw_output = True
                                    else:
                                        saw_output = True
                        except Exception:
                            pass
                        yield event

                if not saw_output:
                    raise EmptyOutputError(
                        f"Empty or missing output for key '{self.output_key}'"
                    )
                return
                
            except (ValidationError, EmptyOutputError) as exc:
                last_error = exc
                if isinstance(exc, EmptyOutputError):
                    last_error_type = "empty_output"
                else:
                    last_error_type = "validation"

                if attempt >= self.max_attempts:
                    break

                # Exponential backoff
                initial_delay = float(getattr(retry_config, "initial_delay", 1.0) or 1.0)
                exp_base = float(getattr(retry_config, "exp_base", 2.0) or 2.0)
                delay = min(10.0, initial_delay * (exp_base ** (attempt - 1)))
                await asyncio.sleep(delay)

        # All retries exhausted - emit error event
        error_payload = {
            "error_type": last_error_type,
            "error_message": str(last_error) if last_error else "Unknown validation error",
            "recoverable": True,
            "suggestion": f"Retry {self.output_key} generation.",
            "attempts": self.max_attempts,
        }
        
        # Add any additional context
        if self.additional_error_info:
            error_payload.update(self.additional_error_info)

        error_key = f"{self.output_key}_error"
        event = Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
        )
        event.actions.state_delta[error_key] = error_payload
        yield event
