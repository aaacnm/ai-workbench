from fastapi.testclient import TestClient

from app.main import app


def test_chinese_question_uses_knowledge_with_mock_model():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "333", "content": "我叫彭健豪。"})
    session = client.post("/api/v1/sessions", json={"title": "name"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "我叫什么", "model_id": "mock"})
    data = response.json()["data"]
    assert "彭健豪" in data["answer"]
    assert data["steps"][0]["type"] == "knowledge_retrieval"
