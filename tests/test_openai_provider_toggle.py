import os

import pytest

from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm

from capstone.services.llm_provider import get_model


def test_get_model_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    model = get_model()
    assert isinstance(model, Gemini)


def test_get_model_openai_uses_litellm(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    model = get_model()
    assert isinstance(model, LiteLlm)
    assert model.model == "gpt-4o-mini"


def test_get_model_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(ValueError):
        _ = get_model()
