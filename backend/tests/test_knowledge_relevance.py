from fastapi.testclient import TestClient

from app.main import app


def test_unrelated_question_does_not_add_knowledge_step():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "wushu.md", "content": "武大郎是武松的哥哥。"})
    session = client.post("/api/v1/sessions", json={"title": "relevance"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "今天适合穿什么颜色", "model_id": "mock"})
    assert not any(step.get("type") == "knowledge_retrieval" for step in response.json()["data"]["steps"])
