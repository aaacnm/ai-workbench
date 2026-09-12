import os
from typing import Any

import httpx
import time

from .base import ModelResponse



class OpenAICompatibleModel:
    """Configuration boundary for OpenAI-compatible providers.

    Network invocation is intentionally deferred until the provider is configured.
    """

    def __init__(self, model_name: str, base_url: str | None = None, api_key_env: str | None = "OPENAI_API_KEY", timeout: float = 30.0, temperature: float = 0.2, max_tokens: int = 1024, client: httpx.Client | None = None, max_retries: int = 2) -> None:
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = client
        self.max_retries = max_retries

    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> ModelResponse:
        api_key = os.getenv(self.api_key_env) if self.api_key_env else None
        if self.api_key_env and not api_key:
            raise RuntimeError(f"未配置模型 API Key 环境变量: {self.api_key_env}")
        payload: dict[str, Any] = {"model": self.model_name, "messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens}
        if tools:
            payload["tools"] = tools
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        client = self.client or httpx.Client(timeout=self.timeout)
        for attempt in range(self.max_retries + 1):
            try:
                response = client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                if response.status_code >= 500 and attempt < self.max_retries:
                    time.sleep(0.1 * (2 ** attempt))
                    continue
                response.raise_for_status()
                try:
                    data = response.json()
                except ValueError as exc:
                    raise RuntimeError(f"模型响应不是有效 JSON（HTTP {response.status_code}）") from exc
                break
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError("模型请求失败") from exc
                time.sleep(0.1 * (2 ** attempt))
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"模型请求失败（HTTP {exc.response.status_code}）") from exc
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("模型响应缺少 choices 字段，可能不兼容 OpenAI 接口")
        choice = choices[0]
        message = choice.get("message", {})
        tool_calls = []
        for call in message.get("tool_calls", []):
            function = call.get("function", {})
            tool_calls.append({"id": call.get("id"), "name": function.get("name"), "arguments": function.get("arguments", "{}")})
        return ModelResponse(message.get("content", ""), tool_calls)
