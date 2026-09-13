from app.knowledge import split_text


def test_split_text_preserves_content_and_overlap():
    chunks = split_text("abcdefghij", chunk_size=6, overlap=2)
    assert chunks == ["abcdef", "efghij"]


def test_split_text_rejects_invalid_options():
    import pytest
    with pytest.raises(ValueError):
        split_text("text", chunk_size=2, overlap=2)
