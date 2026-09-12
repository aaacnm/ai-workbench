from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: Callable[[BaseModel], Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"工具已注册: {definition.name}")
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"工具不存在: {name}") from exc

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        definition = self.get(name)
        validated = definition.input_model.model_validate(payload)
        result = definition.handler(validated)
        return {"tool": name, "input": validated.model_dump(), "output": result, "status": "success"}
