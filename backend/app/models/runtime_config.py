import os
from threading import RLock
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class RuntimeModelUpdate(BaseModel):
    provider: Literal["mock", "openai-compatible", "deepseek", "qwen", "zhipu", "ollama"]
    model_name: str = Field(min_length=1, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=32_000)
    timeout_seconds: float = Field(default=30, ge=1, le=120)


@dataclass
class RuntimeModelState:
    provider: str = "mock"
    model_name: str = "mock"
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout_seconds: float = 30

    def summary(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "api_key_configured": bool(self.api_key),
        }


runtime_model_state = RuntimeModelState()
runtime_model_lock = RLock()


def update_runtime_model(payload: RuntimeModelUpdate) -> dict[str, object]:
    with runtime_model_lock:
        return _update_runtime_model(payload)

def _update_runtime_model(payload: RuntimeModelUpdate) -> dict[str, object]:
    values = payload.model_dump()
    same_profile = payload.provider == runtime_model_state.provider and payload.model_name == runtime_model_state.model_name
    if values.get("api_key") is None and same_profile:
        values["api_key"] = runtime_model_state.api_key
    if not same_profile and values.get("api_key") is None:
        values["api_key"] = None
    for field, value in values.items():
        setattr(runtime_model_state, field, value)
    os.environ["MODEL_PROVIDER"] = payload.provider
    os.environ["MODEL_NAME"] = payload.model_name
    if payload.base_url:
        os.environ["MODEL_BASE_URL"] = payload.base_url
    if payload.provider == "ollama" and payload.base_url:
        os.environ["OLLAMA_BASE_URL"] = payload.base_url
    for provider in ("OPENAI-COMPATIBLE", "DEEPSEEK", "QWEN", "ZHIPU", "OLLAMA"):
        os.environ.pop(f"{provider}_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    if runtime_model_state.api_key:
        os.environ[f"{payload.provider.upper()}_API_KEY"] = runtime_model_state.api_key
        if payload.provider == "openai-compatible":
            os.environ["OPENAI_API_KEY"] = runtime_model_state.api_key
    return runtime_model_state.summary()
