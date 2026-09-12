from dataclasses import dataclass

from app.core.config import ModelConfig, load_model_configs
from .base import ChatModel
from .factory import create_model


@dataclass(frozen=True)
class RegisteredModel:
    config: ModelConfig
    model: ChatModel


class ModelRegistry:
    def __init__(self, entries: list[RegisteredModel] | None = None) -> None:
        if entries is None:
            entries = [RegisteredModel(config, create_model()[1]) for config in load_model_configs()]
        self._entries = {entry.config.id: entry for entry in entries}

    def list(self) -> list[RegisteredModel]:
        return list(self._entries.values())

    def get(self, model_id: str) -> RegisteredModel:
        if model_id not in self._entries:
            raise KeyError(f"模型不存在: {model_id}")
        return self._entries[model_id]

    def status(self, model_id: str) -> dict[str, object]:
        entry = self.get(model_id)
        config = entry.config
        import os
        configured = config.provider == "mock" or config.provider == "ollama" or bool(config.api_key_env and os.getenv(config.api_key_env))
        return {"id": config.id, "provider": config.provider, "configured": configured, "reachable": None, "message": "未执行网络探测"}
