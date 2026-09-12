import os

from .base import ChatModel
from .mock import MockChatModel
from .openai_compatible import OpenAICompatibleModel
from app.core.config import load_model_configs


def create_model() -> tuple[str, ChatModel]:
    provider = os.getenv("MODEL_PROVIDER", "mock").lower()
    if provider in {"openai-compatible", "deepseek", "qwen", "zhipu", "ollama"}:
        api_key_env = None if provider == "ollama" else (f"{provider.upper()}_API_KEY" if provider != "openai-compatible" else "OPENAI_API_KEY")
        base_url = os.getenv("MODEL_BASE_URL") or (os.getenv("OLLAMA_BASE_URL") if provider == "ollama" else os.getenv("OPENAI_BASE_URL"))
        config = load_model_configs()[0]
        return provider, OpenAICompatibleModel(config.model_name, config.base_url, config.api_key_env, config.timeout_seconds, config.temperature, config.max_tokens)
    return "mock", MockChatModel()
