from fastapi.testclient import TestClient

from app.main import app


def test_document_search_returns_ranked_source():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "guide.md", "content": "FastAPI provides APIs. FastAPI is useful."})
    response = client.get("/api/v1/documents/search", params={"q": "FastAPI"})
    assert response.status_code == 200
    result = response.json()["data"][0]
    assert result["filename"] == "guide.md"
    assert result["score"] == 2


def test_document_search_requires_query():
    client = TestClient(app)
    response = client.get("/api/v1/documents/search", params={"q": " "})
    assert response.json()["error"]["code"] == "DOCUMENT_SEARCH_INVALID"
