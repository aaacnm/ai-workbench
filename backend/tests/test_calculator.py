import pytest

from app.tools.calculator import CalculatorError, CalculatorInput, calculate


def test_calculate_basic_expression():
    assert calculate(CalculatorInput(expression="2 + 3 * 4")) == 14


def test_calculate_parentheses_and_power():
    assert calculate(CalculatorInput(expression="(2 + 3) ** 2")) == 25


@pytest.mark.parametrize("expression", ["__import__('os')", "open('x')", "foo + 1", "[1, 2]"])
def test_rejects_unsafe_expression(expression):
    with pytest.raises(CalculatorError):
        calculate(CalculatorInput(expression=expression))


def test_rejects_division_by_zero():
    with pytest.raises(CalculatorError):
        calculate(CalculatorInput(expression="1 / 0"))
