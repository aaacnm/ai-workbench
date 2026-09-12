import os
from typing import Any

import httpx

from .base import ModelResponse


class OpenAICompatibleModel:
    """Configuration boundary for OpenAI-compatible providers.

    Network invocation is intentionally deferred until the provider is configured.
    """

    def __init__(self, model_name: str, base_url: str | None = None, api_key_env: str = "OPENAI_API_KEY", timeout: float = 30.0, client: httpx.Client | None = None) -> None:
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.client = client

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> ModelResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"未配置模型 API Key 环境变量: {self.api_key_env}")
        payload: dict[str, Any] = {"model": self.model_name, "messages": messages}
        if tools:
            payload["tools"] = tools
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        client = self.client or httpx.Client(timeout=self.timeout)
        try:
            response = client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("模型请求失败") from exc
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = []
        for call in message.get("tool_calls", []):
            function = call.get("function", {})
            tool_calls.append({"id": call.get("id"), "name": function.get("name"), "arguments": function.get("arguments", "{}")})
        return ModelResponse(message.get("content", ""), tool_calls)
