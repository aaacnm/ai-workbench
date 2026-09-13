from pathlib import Path

from app.agent.service import AgentService
from app.tools import build_registry


def test_agent_uses_calculator(tmp_path: Path):
    response = AgentService(build_registry(tmp_path)).run("请计算 2 + 3 * 4")
    assert response.answer == "计算结果：14"
    assert response.steps[-1]["tool_name"] == "calculator"


def test_agent_uses_time_tool(tmp_path: Path):
    response = AgentService(build_registry(tmp_path)).run("查询北京时间")
    assert "当前时间" in response.answer
    assert response.steps[-1]["status"] == "success"


def test_agent_reports_unknown_task(tmp_path: Path):
    response = AgentService(build_registry(tmp_path)).run("写一首诗")
    assert "目前可以处理" in response.answer


def test_agent_recognizes_weather_tool(tmp_path: Path, monkeypatch):
    from app.tools.registry import ToolDefinition, ToolRegistry
    from app.tools.weather_tool import WeatherInput
    registry = ToolRegistry()
    registry.register(ToolDefinition("weather", "天气", WeatherInput, lambda payload: {"city": payload.city, "weather": "晴", "temperature": 25, "temperature_unit": "°C", "humidity": 50}))
    response = AgentService(registry).run("查询北京天气")
    assert response.steps[-1]["tool_name"] == "weather"
