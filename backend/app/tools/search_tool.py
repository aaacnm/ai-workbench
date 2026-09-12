from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=5, ge=1, le=10)


class SearchToolError(ValueError):
    """Raised when search input cannot be processed."""


MOCK_RESULTS = [
    {"title": "AI Workbench 文档", "url": "https://example.com/ai-workbench", "snippet": "面向 Agent 工具调用的学习型工作台。"},
    {"title": "FastAPI 文档", "url": "https://fastapi.tiangolo.com/", "snippet": "Python 高性能 Web API 框架。"},
    {"title": "Pydantic 文档", "url": "https://docs.pydantic.dev/", "snippet": "Python 类型校验和数据建模库。"},
]


def search(payload: SearchInput) -> list[dict[str, str]]:
    query = payload.query.casefold()
    if not query.strip():
        raise SearchToolError("搜索关键词不能为空")
    matches = [item for item in MOCK_RESULTS if query in (item["title"] + item["snippet"]).casefold()]
    return (matches or MOCK_RESULTS)[: payload.limit]
