import ast
import operator
from typing import Union

from pydantic import BaseModel, Field


Number = Union[int, float]


class CalculatorInput(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class CalculatorError(ValueError):
    """Raised when an expression is outside the calculator allow-list."""


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise CalculatorError("指数过大")
        return _OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))
    raise CalculatorError("表达式包含不支持的语法")


def calculate(payload: CalculatorInput) -> Number:
    try:
        tree = ast.parse(payload.expression, mode="eval")
        result = _evaluate(tree)
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise CalculatorError("表达式无法计算") from exc
    if isinstance(result, float) and (result != result or abs(result) == float("inf")):
        raise CalculatorError("结果不是有限数字")
    return result
