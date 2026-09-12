from pathlib import Path

import pytest

from app.tools import build_registry
from app.tools.registry import ToolDefinition, ToolRegistry
from app.tools.calculator import CalculatorInput, calculate


def test_registry_lists_and_executes_tools(tmp_path: Path):
    registry = build_registry(tmp_path)
    assert {tool.name for tool in registry.list()} == {"calculator", "time", "search", "file", "code"}
    result = registry.execute("calculator", {"expression": "6 * 7"})
    assert result["output"] == 42
    assert result["status"] == "success"


def test_registry_validates_payload(tmp_path: Path):
    registry = build_registry(tmp_path)
    with pytest.raises(ValueError):
        registry.execute("calculator", {"expression": ""})


def test_registry_rejects_duplicate_and_unknown_tools():
    registry = ToolRegistry()
    definition = ToolDefinition("demo", "demo", CalculatorInput, calculate)
    registry.register(definition)
    with pytest.raises(ValueError):
        registry.register(definition)
    with pytest.raises(KeyError):
        registry.get("missing")
