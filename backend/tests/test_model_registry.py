from app.core.config import ModelConfig
from app.models.mock import MockChatModel
from app.models.registry import ModelRegistry, RegisteredModel
from app.core.config import load_model_configs


def test_registry_lists_metadata():
    entry = RegisteredModel(ModelConfig("demo", "mock", "demo", supports_tools=True, local=True), MockChatModel())
    result = ModelRegistry([entry]).list()[0]
    assert result.config.supports_tools is True
    assert result.config.local is True


def test_registry_rejects_unknown_model():
    try:
        ModelRegistry([]).get("missing")
    except KeyError as exc:
        assert "模型不存在" in str(exc)
    else:
        raise AssertionError("expected KeyError")


def test_provider_config_uses_compatible_adapter(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deepseek")
    monkeypatch.setenv("MODEL_NAME", "deepseek-chat")
    config = load_model_configs()[0]
    assert config.provider == "deepseek"
    assert config.api_key_env == "DEEPSEEK_API_KEY"


def test_model_parameters_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    monkeypatch.setenv("MODEL_TEMPERATURE", "0.7")
    monkeypatch.setenv("MODEL_MAX_TOKENS", "2048")
    config = load_model_configs()[0]
    assert config.temperature == 0.7
    assert config.max_tokens == 2048
