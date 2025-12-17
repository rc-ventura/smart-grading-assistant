"""LiteLLM-based OpenAI client helper.

This is a provider adapter to keep parity with `llm_provider`. It exposes:
- configure_openai_client(api_key, base_url=None)
- get_model(model_name=None, timeout=30)
- generate_json(schema, prompt, model_name=None, temperature=0.4, max_tokens=512)

Environment variables (recommended):
- OPENAI_API_KEY (required for OpenAI/LiteLLM)
- OPENAI_BASE_URL (optional; e.g., LiteLLM proxy or Azure endpoint)

The generate_json helper returns parsed Pydantic objects (schema) and raises on
validation errors, so callers can retry per-criterion without accepting bad JSON.
"""

from __future__ import annotations

import os
from typing import Optional, Type

from litellm import completion
from pydantic import BaseModel, ValidationError
from ..config import DEFAULT_MODEL


def configure_openai_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
    """Set global env for LiteLLM if not already set."""
    if api_key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = api_key
    if base_url and not os.getenv("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = base_url


def get_model(model_name: Optional[str] = None) -> str:
    """Return the model name to use with LiteLLM."""
    # Treat empty env values as missing
    return model_name or (os.getenv("OPENAI_MODEL") or DEFAULT_MODEL)


def _chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 512,
    timeout: int = 30,
) -> str:
    """Execute a chat completion and return the message content."""
    resp = completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    choice = resp.choices[0]
    content = choice.message.get("content", "")
    return content


def generate_json(
    schema: Type[BaseModel],
    prompt: str,
    *,
    model_name: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 512,
    timeout: int = 30,
) -> BaseModel:
    """Call LiteLLM and parse response into the provided Pydantic schema.

    Raises:
        ValueError: if API key is missing
        ValidationError: if schema parsing fails (callers should retry per-criterion)
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

    model = get_model(model_name)
    messages = [{"role": "user", "content": prompt}]
    raw = _chat_completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    try:
        return schema.model_validate_json(raw)
    except ValidationError:
        raise


__all__ = ["configure_openai_client", "get_model", "generate_json"]
