import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class ModelConfig:
    id: str
    provider: str
    model_name: str
    base_url: str | None = None
    api_key_env: str | None = None
    supports_tools: bool = True
    local: bool = False
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout_seconds: float = 30.0


def load_model_configs() -> list[ModelConfig]:
    provider = os.getenv("MODEL_PROVIDER", "mock").lower()
    model_name = os.getenv("MODEL_NAME", "mock")
    temperature = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "1024"))
    timeout = float(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))
    if provider == "ollama":
        return [ModelConfig("ollama", "ollama", model_name, os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), None, True, True, temperature, max_tokens, timeout)]
    if provider in {"deepseek", "qwen", "zhipu"}:
        defaults = {"deepseek": "https://api.deepseek.com/v1", "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1", "zhipu": "https://open.bigmodel.cn/api/paas/v4"}
        return [ModelConfig(provider, provider, model_name, os.getenv("MODEL_BASE_URL", defaults[provider]), f"{provider.upper()}_API_KEY", True, False, temperature, max_tokens, timeout)]
    if provider == "openai-compatible":
        return [ModelConfig("openai-compatible", provider, model_name, os.getenv("OPENAI_BASE_URL"), "OPENAI_API_KEY", True, False)]
    return [ModelConfig("mock", "mock", "mock", None, None, True, True, temperature, max_tokens, timeout)]
