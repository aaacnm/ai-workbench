import os
from dataclasses import dataclass

from pydantic import BaseModel, Field


class RuntimeModelUpdate(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
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


def update_runtime_model(payload: RuntimeModelUpdate) -> dict[str, object]:
    values = payload.model_dump()
    if values.get("api_key") is None:
        values["api_key"] = runtime_model_state.api_key
    for field, value in values.items():
        setattr(runtime_model_state, field, value)
    os.environ["MODEL_PROVIDER"] = payload.provider
    os.environ["MODEL_NAME"] = payload.model_name
    if payload.base_url:
        os.environ["MODEL_BASE_URL"] = payload.base_url
    if payload.provider == "ollama" and payload.base_url:
        os.environ["OLLAMA_BASE_URL"] = payload.base_url
    if runtime_model_state.api_key:
        os.environ[f"{payload.provider.upper()}_API_KEY"] = runtime_model_state.api_key
        os.environ["OPENAI_API_KEY"] = runtime_model_state.api_key
    return runtime_model_state.summary()
