import os

from .base import ChatModel
from .mock import MockChatModel
from .openai_compatible import OpenAICompatibleModel


def create_model() -> tuple[str, ChatModel]:
    provider = os.getenv("MODEL_PROVIDER", "mock").lower()
    if provider == "openai-compatible":
        return "openai-compatible", OpenAICompatibleModel(os.getenv("MODEL_NAME", "gpt-4o-mini"))
    return "mock", MockChatModel()
