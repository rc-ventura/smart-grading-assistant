import types as py_types

import pytest

from google.adk.models.google_llm import Gemini
from google.genai import types

from services.gemini_client import (
    get_model,
    get_agent_generate_config,
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

    captured = {}

    class DummyGemini:
        def __init__(self, *, model: str, retry_options):
            captured["model"] = model
            captured["retry_options"] = retry_options

    monkeypatch.setattr(
        "capstone.services.gemini_client.Gemini",
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


def test_get_ui_model_passes_generation_config(monkeypatch):
    """get_ui_model must pass temperature/tokens for GenerationConfig."""

    captured = {}

    class DummyGenerativeModel:
        def __init__(self, model, generation_config=None):
            captured["model"] = model
            captured["generation_config"] = generation_config

    monkeypatch.setattr(
        "capstone.services.gemini_client.genai.GenerativeModel",
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
