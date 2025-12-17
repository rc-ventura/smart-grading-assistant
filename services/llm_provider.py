import logging
from math import log
from typing import Optional
import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.models.google_llm import Gemini
import google.generativeai as genai
from google.genai import types
from google.genai.types import GenerationConfig
from ..config import (
    MODEL,
    MODEL_LITE,
    retry_config,
    LLM_PROVIDER,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    GRADER_TEMPERATURE,
    GRADER_MAX_OUTPUT_TOKENS,
    FEEDBACK_TEMPERATURE,
    FEEDBACK_MAX_OUTPUT_TOKENS,
    OPENAI_GPT5_MIN_OUTPUT_TOKENS,
)

DEFAULT_SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    )
]


def get_model():
    """Return a configured Gemini model for all ADK agents.

    For now, this always uses the lightweight model defined by MODEL_LITE.
    If you later decide to use different models per agent, centralize that
    logic here without changing call sites.
    """
    provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set when LLM_PROVIDER=openai")

        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = api_key

        base_url = (os.getenv("OPENAI_BASE_URL") or OPENAI_BASE_URL or "").strip()
        if base_url and not os.getenv("OPENAI_BASE_URL"):
            os.environ["OPENAI_BASE_URL"] = base_url

        model_name = (os.getenv("OPENAI_MODEL") or "").strip() or OPENAI_MODEL
        if model_name.startswith("gpt-5") and "/" not in model_name:
            model_name = f"openai/{model_name}"

        logging.info(f"Using OpenAI model: {model_name}")
        return LiteLlm(model=model_name, drop_params=True)

    logging.info(f"Using Gemini model: {MODEL}")
    return Gemini(model=MODEL, retry_options=retry_config)


def get_agent_generate_config(
    *,
    temperature: float = 0.7,
    max_output_tokens: int = 1024,
    top_p: float = None,
    top_k: Optional[float] = None,
    safety_settings: Optional[list[types.SafetySetting]] = None,
) -> types.GenerateContentConfig:
    """Default generation config for all ADK agents.

    Central place to tune temperature, token limits and safety settings.
    """
    return types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=top_p,
        top_k=top_k,
        safety_settings=safety_settings or DEFAULT_SAFETY_SETTINGS,
    )


def get_agent_generate_config_for(agent_kind: str) -> types.GenerateContentConfig:
    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER or "gemini").strip().lower()
    kind = (agent_kind or "").strip().lower()

    if kind == "grader":
        if provider != "openai":
            return get_agent_generate_config()
        temperature = float(os.getenv("GRADER_TEMPERATURE", str(GRADER_TEMPERATURE)))
        max_output_tokens = int(
            os.getenv("GRADER_MAX_OUTPUT_TOKENS", str(GRADER_MAX_OUTPUT_TOKENS))
        )
    elif kind == "feedback":
        if provider not in ("openai", "gemini"):
            return get_agent_generate_config()
        temperature = float(os.getenv("FEEDBACK_TEMPERATURE", str(FEEDBACK_TEMPERATURE)))
        max_output_tokens = int(
            os.getenv("FEEDBACK_MAX_OUTPUT_TOKENS", str(FEEDBACK_MAX_OUTPUT_TOKENS))
        )
    else:
        return get_agent_generate_config()

    if provider == "openai":
        openai_model = (os.getenv("OPENAI_MODEL") or "").strip() or OPENAI_MODEL
        openai_model_name = openai_model.split("/")[-1] if openai_model else ""
        if openai_model_name.startswith("gpt-5"):
            min_output_tokens = int(
                os.getenv(
                    "OPENAI_GPT5_MIN_OUTPUT_TOKENS",
                    str(OPENAI_GPT5_MIN_OUTPUT_TOKENS),
                )
            )
            max_output_tokens = max(max_output_tokens, min_output_tokens)

    return get_agent_generate_config(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def get_ui_model(
    *,
    model_name: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 1024,
    top_p: float = None,
    top_k: Optional[int] = None,
) -> genai.GenerativeModel:
    """Return a GenerativeModel instance for UI or non-ADK use.

    Call configure_ui_client(api_key) once before using this helper.
    """
    generation_config = GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=top_p,
        top_k=top_k,
    )

    return genai.GenerativeModel(model_name or MODEL, generation_config=generation_config)
