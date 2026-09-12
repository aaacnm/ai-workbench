import pytest

from app.tools.code_tool import CodeInput, CodeToolError, execute_restricted


def test_code_tool_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_CODE_TOOL", raising=False)
    with pytest.raises(CodeToolError, match="默认关闭"):
        execute_restricted(CodeInput(expression="1 + 1"))


def test_code_tool_rejects_calls_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_CODE_TOOL", "true")
    with pytest.raises(CodeToolError, match="基础算术"):
        execute_restricted(CodeInput(expression="__import__('os')"))


def test_code_tool_runs_allowlisted_expression(monkeypatch):
    monkeypatch.setenv("ENABLE_CODE_TOOL", "true")
    result = execute_restricted(CodeInput(expression="2 ** 3"))
    assert result["output"] == "8"
