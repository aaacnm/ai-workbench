from fastapi.testclient import TestClient

from app.main import app


def test_message_records_knowledge_retrieval_step():
    client = TestClient(app)
    document = client.post("/api/v1/documents", json={"filename": "faq.md", "content": "AI Workbench supports document retrieval."}).json()["data"]
    session = client.post("/api/v1/sessions", json={"title": "knowledge"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "document retrieval", "model_id": "mock"})
    assert response.status_code == 200
    assert response.json()["data"]["steps"][0]["type"] == "knowledge_retrieval"
