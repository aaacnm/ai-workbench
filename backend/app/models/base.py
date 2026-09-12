from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ModelResponse:
    content: str
    tool_calls: list[dict[str, Any]]


class ChatModel(Protocol):
    def chat(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> ModelResponse:
        ...
