import re
from dataclasses import dataclass
from typing import Any

from app.tools.registry import ToolRegistry
from app.models.base import ChatModel
import json
import os


@dataclass
class AgentResponse:
    answer: str
    steps: list[dict[str, Any]]
    model: str = "rule-based"


class AgentService:
    def __init__(self, registry: ToolRegistry, model: ChatModel | None = None, model_name: str = "rule-based") -> None:
        self.registry = registry
        self.model = model
        self.model_name = model_name

    def run(self, content: str) -> AgentResponse:
        text = content.strip()
        if not text:
            return AgentResponse("请输入任务内容。", [], self.model_name)
        if any(word in text for word in ("时间", "几点", "日期")):
            timezone = "Asia/Shanghai" if "上海" in text or "北京时间" in text else "UTC"
            return self._execute("time", {"timezone": timezone}, "我识别到这是时间查询任务。", lambda out: f"当前时间（{out['timezone']}）：{out['formatted']}")
        if any(word in text for word in ("天气", "气温", "温度")):
            city_match = re.search(r"([\u4e00-\u9fff]{2,10})(?:的)?(?:天气|气温|温度)", text)
            city = city_match.group(1) if city_match else "北京"
            return self._execute("weather", {"city": city}, "我识别到这是天气查询任务。", lambda out: f"{out['city']}当前天气：{out['weather']}，温度 {out['temperature']}{out['temperature_unit']}，湿度 {out['humidity']}%。")
        expression = self._extract_expression(text)
        if expression:
            return self._execute("calculator", {"expression": expression}, "我识别到这是数学计算任务。", lambda out: f"计算结果：{out}")
        if "搜索" in text or "查找" in text:
            query = re.sub(r"^(请)?(搜索|查找)", "", text).strip() or text
            return self._execute("search", {"query": query}, "我识别到这是搜索任务。", lambda out: "搜索结果：" + "；".join(item["title"] for item in out))
        return AgentResponse("我目前可以处理时间查询、数学计算和 Mock 搜索。请明确描述任务。", [{"type": "summary", "content": "未匹配到可用工具"}], self.model_name)

    def run_with_model(self, content: str, history: list[dict[str, str]] | None = None) -> AgentResponse:
        """Run the provider tool-call protocol when a model is configured."""
        if self.model is None:
            return self.run(content)
        if content.startswith("[KNOWLEDGE_CONTEXT]") and "\n[QUESTION]\n" in content:
            context, question = content.split("\n[QUESTION]\n", 1)
            messages = [
                {"role": "system", "content": "You are a grounded assistant. When knowledge context is provided, use it as the primary source, synthesize a clear answer, cite the source filename, and never claim ignorance if the context directly answers the question. Do not invent facts beyond the context."},
                {"role": "user", "content": f"Knowledge context:\n{context.replace('[KNOWLEDGE_CONTEXT]\n', '')}\n\nQuestion: {question}"},
            ]
        else:
            messages = list(history or []) + [{"role": "user", "content": content}]
        definitions = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_model.model_json_schema()}} for t in self.registry.list() if t.name != "code" or os.getenv("ENABLE_CODE_TOOL", "false").lower() == "true"]
        steps: list[dict[str, Any]] = []
        for _ in range(3):
            response = self.model.chat(messages, definitions)
            if not response.tool_calls:
                return AgentResponse(response.content, steps, self.model_name)
            messages.append({"role": "assistant", "content": response.content or "", "tool_calls": [{"id": call.get("id") or f"call_{index}", "type": "function", "function": {"name": call.get("name"), "arguments": call.get("arguments", "{}")}} for index, call in enumerate(response.tool_calls)]})
            for call in response.tool_calls:
                name = call.get("name", "")
                try:
                    payload = json.loads(call.get("arguments", "{}"))
                    result = self.registry.execute(name, payload)
                    steps.append({"type": "tool_call", "tool_name": name, "input": payload, "output": result["output"], "status": "success"})
                    messages.append({"role": "tool", "tool_call_id": call.get("id") or name, "name": name, "content": json.dumps(result["output"], ensure_ascii=False)})
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    steps.append({"type": "tool_call", "tool_name": name, "status": "error", "error": str(exc)})
                    messages.append({"role": "tool", "tool_call_id": call.get("id") or name, "name": name, "content": json.dumps({"error": str(exc)}, ensure_ascii=False)})
        return AgentResponse("工具调用次数超过限制，请缩小任务范围。", steps, self.model_name)

    @staticmethod
    def _extract_expression(text: str) -> str | None:
        match = re.search(r"[\d\s+\-*/().%]+", text)
        expression = match.group(0).strip() if match else ""
        return expression if any(char.isdigit() for char in expression) and any(op in expression for op in "+-*/%") else None

    def _execute(self, name: str, payload: dict[str, Any], summary: str, answer_builder) -> AgentResponse:
        steps = [{"type": "summary", "content": summary}, {"type": "tool_call", "tool_name": name, "input": payload, "status": "running"}]
        try:
            result = self.registry.execute(name, payload)
        except (ValueError, KeyError) as exc:
            steps[-1].update({"status": "error", "error": str(exc)})
            return AgentResponse(f"工具执行失败：{exc}", steps, self.model_name)
        steps[-1].update({"output": result["output"], "status": "success"})
        return AgentResponse(answer_builder(result["output"]), steps, self.model_name)
