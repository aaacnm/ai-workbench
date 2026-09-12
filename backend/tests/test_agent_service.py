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
