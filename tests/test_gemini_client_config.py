import types as py_types
import os

import pytest

from google.adk.models.google_llm import Gemini
from google.genai import types

from services.llm_provider import (
    get_model,
    get_agent_generate_config,
    get_agent_generate_config_for,
    get_ui_model,
)
from config import MODEL, retry_config
from agents.graders import create_criterion_grader


@pytest.fixture
def dummy_retry_config():
    # Use the real retry_config only to check that it is propagated
    return retry_config


def test_get_model_uses_global_model_and_retry(monkeypatch, dummy_retry_config):
    """get_model must build Gemini with MODEL and retry_config globals."""

    # Ensure local env doesn't switch provider to OpenAI during this test.
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    captured = {}

    class DummyGemini:
        def __init__(self, *, model: str, retry_options):
            captured["model"] = model
            captured["retry_options"] = retry_options

    monkeypatch.setattr(
        "services.llm_provider.Gemini",
        DummyGemini,
    )

    result = get_model()

    # A função deve retornar a instância criada
    assert isinstance(result, DummyGemini)
    assert captured["model"] == MODEL
    assert captured["retry_options"] is dummy_retry_config


def test_get_agent_generate_config_defaults():
    """get_agent_generate_config must apply the expected defaults."""

    cfg = get_agent_generate_config()

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.temperature == 0.7
    assert cfg.max_output_tokens == 1024
    assert cfg.top_p is None
    assert cfg.top_k is None
    # Default safety settings should be applied
    assert cfg.safety_settings is not None
    assert len(cfg.safety_settings) >= 1
    first = cfg.safety_settings[0]
    assert first.category == types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
    assert first.threshold == types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE


def test_get_agent_generate_config_custom_values():
    """get_agent_generate_config must accept parameter overrides."""

    cfg = get_agent_generate_config(
        temperature=0.3,
        max_output_tokens=256,
        top_p=0.9,
        top_k=42,
    )

    assert cfg.temperature == 0.3
    assert cfg.max_output_tokens == 256
    assert cfg.top_p == 0.9
    assert cfg.top_k == 42


def test_get_agent_generate_config_for_grader_defaults_to_shared_config(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    cfg = get_agent_generate_config_for("grader")

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.temperature == 0.7
    assert cfg.max_output_tokens == 1024


def test_get_agent_generate_config_for_grader_openai_uses_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("GRADER_TEMPERATURE", "0.11")
    monkeypatch.setenv("GRADER_MAX_OUTPUT_TOKENS", "123")

    cfg = get_agent_generate_config_for("grader")

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.temperature == pytest.approx(0.11)
    assert cfg.max_output_tokens == 123


def test_get_agent_generate_config_for_grader_openai_gpt5_enforces_min(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("GRADER_MAX_OUTPUT_TOKENS", "384")
    monkeypatch.setenv("OPENAI_GPT5_MIN_OUTPUT_TOKENS", "2048")

    cfg = get_agent_generate_config_for("grader")

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.max_output_tokens == 2048


def test_get_agent_generate_config_for_feedback_gemini_uses_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("FEEDBACK_TEMPERATURE", "0.6")
    monkeypatch.setenv("FEEDBACK_MAX_OUTPUT_TOKENS", "1500")

    cfg = get_agent_generate_config_for("feedback")

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.temperature == pytest.approx(0.6)
    assert cfg.max_output_tokens == 1500


def test_get_agent_generate_config_for_feedback_openai_gpt5_enforces_min(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    monkeypatch.setenv("FEEDBACK_MAX_OUTPUT_TOKENS", "512")
    monkeypatch.setenv("OPENAI_GPT5_MIN_OUTPUT_TOKENS", "2048")

    cfg = get_agent_generate_config_for("feedback")

    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.max_output_tokens == 2048


def test_get_ui_model_passes_generation_config(monkeypatch):
    """get_ui_model must pass temperature/tokens for GenerationConfig."""

    captured = {}

    class DummyGenerativeModel:
        def __init__(self, model, generation_config=None):
            captured["model"] = model
            captured["generation_config"] = generation_config

    monkeypatch.setattr(
        "services.llm_provider.genai.GenerativeModel",
        DummyGenerativeModel,
    )

    model = get_ui_model(
        temperature=0.4,
        max_output_tokens=512,
        top_p=0.8,
        top_k=10,
    )

    assert isinstance(model, DummyGenerativeModel)

    gen_cfg = captured["generation_config"]
    assert isinstance(gen_cfg, types.GenerationConfig)
    assert gen_cfg.temperature == 0.4
    assert gen_cfg.max_output_tokens == 512
    assert gen_cfg.top_p == 0.8
    assert gen_cfg.top_k == 10


def test_create_criterion_grader_uses_shared_model_and_config():
    """Grader created must use get_model + get_agent_generate_config."""

    # Ensure local env doesn't switch provider to OpenAI during this test.
    os.environ["LLM_PROVIDER"] = "gemini"

    grader = create_criterion_grader(
        "Code Quality",
        "Evaluate code quality",
        30,
    )

    # Model must a  Gemini configured
    assert isinstance(grader.model, Gemini)
    assert grader.model.model == MODEL
    assert grader.model.retry_options is retry_config

    # generate_content_config must vir de get_agent_generate_config
    assert isinstance(grader.generate_content_config, types.GenerateContentConfig)
    assert grader.generate_content_config.temperature == pytest.approx(0.7)
    assert grader.generate_content_config.max_output_tokens == 1024
