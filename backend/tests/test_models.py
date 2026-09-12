import pytest
import httpx

from app.models.factory import create_model
from app.models.openai_compatible import OpenAICompatibleModel
from app.models.base import ModelResponse


def test_default_model_is_mock(monkeypatch):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    name, model = create_model()
    assert name == "mock"
    assert model.chat([]).content


def test_openai_model_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    model = OpenAICompatibleModel("demo")
    with pytest.raises(RuntimeError, match="API Key"):
        model.chat([])


def test_openai_compatible_parses_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello", "tool_calls": [{"id": "1", "function": {"name": "time", "arguments": "{}"}}]}}]})

    model = OpenAICompatibleModel("demo", base_url="http://test", client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = model.chat([{"role": "user", "content": "time"}])
    assert isinstance(result, ModelResponse)
    assert result.content == "hello"
    assert result.tool_calls[0]["name"] == "time"


def test_openai_compatible_retries_server_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    model = OpenAICompatibleModel("demo", base_url="http://test", client=httpx.Client(transport=httpx.MockTransport(handler)), max_retries=1)
    assert model.chat([]).content == "ok"
    assert attempts["count"] == 2
