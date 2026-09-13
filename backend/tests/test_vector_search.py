from fastapi.testclient import TestClient

from app.main import app


def test_vector_search_returns_similarity_scores():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "retrieval.md", "content": "Vector retrieval finds related knowledge."})
    response = client.get("/api/v1/documents/search", params={"q": "related knowledge", "mode": "vector", "limit": 50})
    assert response.status_code == 200
    results = response.json()["data"]
    result = next(item for item in results if item["filename"] == "retrieval.md")
    assert -1 <= result["score"] <= 1


def test_vector_search_ranks_relevant_chinese_document_first():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "noise-cn.md", "content": "苹果公司发布了新手机。"})
    client.post("/api/v1/documents", json={"filename": "name-cn.md", "content": "我叫彭健豪，来自杭州。"})
    response = client.get("/api/v1/documents/search", params={"q": "我叫什么名字", "mode": "vector", "limit": 50})
    results = response.json()["data"]
    assert results
    assert results[0]["filename"] == "name-cn.md"
