"""Built-in tools for the AI Workbench."""

from pathlib import Path

from .calculator import CalculatorInput, calculate
from .code_tool import CodeInput, execute_restricted
from .file_tool import FileInput, read_workspace_file
from .registry import ToolDefinition, ToolRegistry
from .search_tool import SearchInput, search
from .time_tool import TimeInput, current_time


def build_registry(workspace_root: Path) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolDefinition("calculator", "安全数学计算", CalculatorInput, calculate))
    registry.register(ToolDefinition("code", "默认关闭的受限代码执行", CodeInput, execute_restricted))
    registry.register(ToolDefinition("time", "查询当前时间", TimeInput, current_time))
    registry.register(ToolDefinition("search", "Mock 网络搜索", SearchInput, search))
    registry.register(
        ToolDefinition(
            "file",
            "读取工作目录内的文本文件",
            FileInput,
            lambda payload: read_workspace_file(payload, workspace_root),
        )
    )
    return registry
