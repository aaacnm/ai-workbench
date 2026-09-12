import os

import pytest


@pytest.fixture(autouse=True)
def isolate_model_environment(monkeypatch: pytest.MonkeyPatch):
    """Keep tests offline and independent from the developer's .env file."""
    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    monkeypatch.setenv("MODEL_NAME", "mock")
    monkeypatch.delenv("MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("CONFIG_ENCRYPTION_KEY", raising=False)
    import app.main as main
    from app.agent.service import AgentService
    from app.models.mock import MockChatModel
    from app.models.registry import ModelRegistry, RegisteredModel
    from app.core.config import ModelConfig
    main.model_name = "mock"
    main.chat_model = MockChatModel()
    main.model_registry = ModelRegistry([RegisteredModel(ModelConfig("mock", "mock", "mock", local=True), main.chat_model)])
    main.agent_service = AgentService(main.tool_registry, main.chat_model, "mock")
