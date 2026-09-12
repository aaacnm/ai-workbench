from app.tools.search_tool import SearchInput, search


def test_search_returns_matching_results():
    results = search(SearchInput(query="FastAPI"))
    assert results[0]["title"] == "FastAPI 文档"


def test_search_respects_limit():
    assert len(search(SearchInput(query="anything", limit=2))) == 2
