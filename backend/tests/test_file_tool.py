from pathlib import Path

import pytest

from app.tools.file_tool import FileInput, FileToolError, read_workspace_file


def test_reads_file_inside_workspace(tmp_path: Path):
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    result = read_workspace_file(FileInput(path="note.txt"), tmp_path)
    assert result["content"] == "hello"
    assert result["truncated"] is False


def test_rejects_path_traversal(tmp_path: Path):
    with pytest.raises(FileToolError, match="工作目录"):
        read_workspace_file(FileInput(path="../secret.txt"), tmp_path)


def test_limits_content_length(tmp_path: Path):
    (tmp_path / "long.txt").write_text("abcdef", encoding="utf-8")
    result = read_workspace_file(FileInput(path="long.txt", max_chars=3), tmp_path)
    assert result["content"] == "abc"
    assert result["truncated"] is True


def test_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileToolError, match="不存在"):
        read_workspace_file(FileInput(path="missing.txt"), tmp_path)
