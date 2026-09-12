from pathlib import Path

from app.agent.service import AgentService
from app.models.base import ModelResponse
from app.tools import build_registry


class FakeToolCallingModel:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            return ModelResponse("", [{"name": "calculator", "arguments": '{"expression":"6 * 7"}'}])
        assert messages[-1]["role"] == "tool"
        return ModelResponse("工具计算结果是 42。", [])


def test_model_tool_call_loop_executes_and_returns_answer(tmp_path: Path):
    model = FakeToolCallingModel()
    response = AgentService(build_registry(tmp_path), model, "fake").run_with_model("算一下")
    assert response.answer == "工具计算结果是 42。"
    assert response.steps[0]["tool_name"] == "calculator"
    assert response.steps[0]["output"] == 42
