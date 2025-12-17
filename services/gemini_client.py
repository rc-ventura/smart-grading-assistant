from typing import Optional

from google.adk.models.google_llm import Gemini
import google.generativeai as genai
from google.genai import types

from config import MODEL, MODEL_LITE, retry_config

DEFAULT_SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    )
]


def get_model() -> Gemini:
    """Return a configured Gemini model for all ADK agents.

    For now, this always uses the lightweight model defined by MODEL_LITE.
    If you later decide to use different models per agent, centralize that
    logic here without changing call sites.
    """
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



def get_ui_model(
    *,
    temperature: float = 0.7,
    max_output_tokens: int = 1024,
    top_p: float = None,
    top_k: Optional[int] = None,
) -> genai.GenerativeModel:
    """Return a GenerativeModel instance for UI interactions.

    The API key must be configured separately via ``configure_ui_client``.
    Tune temperature / tokens centrally here.
    """
    generation_config = types.GenerationConfig(
        temperature=temperature,
        maxOutputTokens=max_output_tokens,
        topP=top_p,
        topK=top_k,
    )

    # For now, reuse MODEL_LITE here as well. Adjust in one place if needed.
    return genai.GenerativeModel(MODEL, generation_config=generation_config)
