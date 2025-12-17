import json

import pytest
from pydantic import BaseModel, ValidationError

from capstone.services import openai_client


class DummySchema(BaseModel):
    a: int


class _DummyChoice:
    def __init__(self, content: str):
        self.message = {"content": content}


class _DummyResp:
    def __init__(self, content: str):
        self.choices = [_DummyChoice(content)]


def test_generate_json_parses_valid_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_completion(**kwargs):
        return _DummyResp(json.dumps({"a": 123}))

    monkeypatch.setattr(openai_client, "completion", fake_completion)

    result = openai_client.generate_json(DummySchema, "prompt")
    assert result.a == 123


def test_generate_json_raises_on_invalid_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_completion(**kwargs):
        return _DummyResp("{invalid json")

    monkeypatch.setattr(openai_client, "completion", fake_completion)

    with pytest.raises(ValidationError):
        _ = openai_client.generate_json(DummySchema, "prompt")


def test_generate_json_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        _ = openai_client.generate_json(DummySchema, "prompt")
