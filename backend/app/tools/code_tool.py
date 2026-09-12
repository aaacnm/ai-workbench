import ast
import os
import subprocess
import sys

from pydantic import BaseModel, Field


class CodeInput(BaseModel):
    expression: str = Field(min_length=1, max_length=200)
    timeout_seconds: float = Field(default=2.0, ge=0.1, le=5.0)


class CodeToolError(ValueError):
    """Raised when restricted code execution is unavailable or unsafe."""


def _validate_expression(expression: str) -> None:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CodeToolError("代码不是有效表达式") from exc
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Expression, ast.Constant, ast.UnaryOp, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.USub, ast.UAdd)):
            raise CodeToolError("仅允许数字和基础算术表达式")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise CodeToolError("仅允许数字常量")


def execute_restricted(payload: CodeInput) -> dict[str, object]:
    if os.getenv("ENABLE_CODE_TOOL", "false").lower() != "true":
        raise CodeToolError("代码工具默认关闭，请设置 ENABLE_CODE_TOOL=true 后再启用")
    _validate_expression(payload.expression)
    command = [sys.executable, "-I", "-c", f"print({payload.expression})"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=payload.timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CodeToolError("代码执行超时") from exc
    if completed.returncode != 0:
        raise CodeToolError("代码执行失败")
    return {"expression": payload.expression, "output": completed.stdout[:2_000].strip(), "warning": "仅适合本地演示，不是生产级沙箱"}
