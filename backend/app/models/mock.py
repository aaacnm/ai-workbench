from typing import Any

from .base import ModelResponse


class MockChatModel:
    """Offline model used for local development and tests."""

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> ModelResponse:
        return ModelResponse("Mock 模型尚未接入真实推理。", [])
