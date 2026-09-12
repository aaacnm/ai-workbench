from pathlib import Path

from pydantic import BaseModel, Field


class FileInput(BaseModel):
    path: str = Field(min_length=1, max_length=260)
    max_chars: int = Field(default=10_000, ge=1, le=50_000)


class FileToolError(ValueError):
    """Raised when a workspace file cannot be read safely."""


def read_workspace_file(payload: FileInput, workspace_root: Path) -> dict:
    root = workspace_root.resolve()
    candidate = (root / payload.path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise FileToolError("文件路径必须位于工作目录内") from exc
    if not candidate.exists() or not candidate.is_file():
        raise FileToolError("文件不存在")
    if candidate.stat().st_size > 1_000_000:
        raise FileToolError("文件超过 1 MB 大小限制")
    try:
        content = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise FileToolError("仅支持 UTF-8 文本文件") from exc
    return {
        "path": payload.path,
        "content": content[: payload.max_chars],
        "truncated": len(content) > payload.max_chars,
    }
