"""Rubric Guardrail Plugin - ensures rubric is validated before grading."""

import json
import logging
from typing import Any, Optional

from google.adk.agents import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types


class RubricGuardrailPlugin(BasePlugin):
    """Guardrail to ensure rubric is valid before running grading agents.

    This plugin runs before each agent. For agents that depend on a validated
    rubric, it checks the session state for a `validation_result` with status == "valid".
    
    Pattern: Uses before_agent_callback to return types.Content which skips
    the agent's execution gracefully without crashing the app.
    """

    def __init__(self, build_graders_fn=None) -> None:
        super().__init__(name="rubric_guardrail")
        self._blocked_agents: set = set()
        self._build_graders_fn = build_graders_fn  # Injected dependency

    def _normalize_validation_payload(self, payload: Any) -> Optional[dict]:
        """Normalize different payload formats into a dict or None."""
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            text = payload.lower()
            if any(keyword in text for keyword in ["invalid", "error", "missing", "failed"]):
                return {
                    "status": "invalid",
                    "errors": ["Rubric validation failed - see validator response"],
                }
            if "valid" in text and "invalid" not in text:
                return {"status": "valid"}
        return None

    def _get_state_dict(self, callback_context: CallbackContext) -> dict:
        """Safely get state as dict from callback_context."""
        try:
            return callback_context.state.to_dict()
        except Exception:
            return {}

    def _get_rubric(self, callback_context: CallbackContext) -> Optional[dict]:
        """Get the latest rubric dict from state or invocation context."""
        state_dict = self._get_state_dict(callback_context)
        rubric = state_dict.get("rubric")
        if isinstance(rubric, dict):
            return rubric
        inv_ctx = getattr(callback_context, "_invocation_context", None)
        if inv_ctx:
            session_state = getattr(inv_ctx, "session_state", {}) or {}
            rubric = session_state.get("rubric")
            if isinstance(rubric, dict):
                return rubric
        return None

    def _get_validation_result(self, callback_context: CallbackContext) -> Optional[dict]:
        """Extract rubric validation status from session state."""
        state_sources = []

        try:
            state_sources.append(callback_context.state.to_dict())
        except Exception:
            pass

        inv_ctx = getattr(callback_context, "_invocation_context", None)
        if inv_ctx:
            session_state = getattr(inv_ctx, "session_state", {}) or {}
            state_sources.append(session_state)

        for source in state_sources:
            if not source:
                continue
            for key in ("rubric_validation", "validation_result"):
                if key in source:
                    normalized = self._normalize_validation_payload(source.get(key))
                    if normalized:
                        return normalized
        return None

    def _is_rubric_valid(self, callback_context: CallbackContext) -> bool:
        """Check if rubric has been validated successfully."""
        validation_result = self._get_validation_result(callback_context)
        if validation_result is None:
            return False
        return validation_result.get("status") == "valid"

    def _ensure_dynamic_graders(self, agent: BaseAgent, callback_context: CallbackContext) -> None:
        """Inject dynamic graders based on rubric criteria."""
        if not self._build_graders_fn:
            return
        rubric = self._get_rubric(callback_context)
        if not rubric:
            return
        dynamic_graders, grade_keys = self._build_graders_fn(rubric)
        if not dynamic_graders:
            return
        agent.sub_agents = dynamic_graders
        try:
            callback_context.state["grader_output_keys"] = grade_keys
        except Exception:
            pass

    def _build_block_message(self, agent_name: str, callback_context: CallbackContext) -> str:
        """Build a user-friendly blocking message."""
        validation_result = self._get_validation_result(callback_context)
        errors = []
        if validation_result:
            errors = validation_result.get("errors", [])
        
        error_details = "\n".join(f"  - {e}" for e in errors) if errors else "  - Rubric was not validated"
        
        return f"""
🚫 **GRADING BLOCKED BY GUARDRAIL**

Agent '{agent_name}' cannot proceed because the rubric validation failed.

**Validation Errors:**
{error_details}

**What to do:**
1. Review the rubric structure
2. Ensure all required fields are present (name, criteria with name/max_score/description)
3. Submit a corrected rubric

No grading was performed. The pipeline has been safely stopped.
"""

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        """Block grading agents when rubric is not valid."""
        protected_agents = {
            "ParallelGraders",
            "AggregatorAgent",
            "ApprovalAgent",
            "FeedbackGeneratorAgent",
            "Grader_Code_Quality",
            "Grader_Functionality",
            "Grader_Documentation",
        }

        if agent.name not in protected_agents:
            return None

        validation_result = self._get_validation_result(callback_context)
        print(f"[RubricGuardrail] before_agent_callback - agent={agent.name}, validation_result={validation_result}")

        if validation_result and validation_result.get("status") == "valid":
            if agent.name == "ParallelGraders":
                self._ensure_dynamic_graders(agent, callback_context)
            print(f"[RubricGuardrail] ALLOW agent '{agent.name}' (rubric valid)")
            return None

        self._blocked_agents.add(agent.name)
        logging.warning("[RubricGuardrail] BLOCKED agent '%s' - rubric not valid.", agent.name)
        print(f"[RubricGuardrail] BLOCK agent '{agent.name}' (rubric invalid or missing)")

        return types.Content(
            role="model",
            parts=[types.Part(text=self._build_block_message(agent.name, callback_context))],
        )
