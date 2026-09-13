from fastapi.testclient import TestClient

from app.main import app


def test_hyphenated_model_name_is_not_treated_as_arithmetic():
    client = TestClient(app)
    client.post("/api/v1/documents", json={"filename": "pricing.md", "content": "gpt-4o 的价格是 100 元。"})
    session = client.post("/api/v1/sessions", json={"title": "routing"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "gpt-4o 的价格", "model_id": "mock"})
    steps = response.json()["data"]["steps"]
    assert not any(step.get("reason") == "arithmetic_intent" for step in steps)


def test_tool_intent_exposes_retrieval_skip_step():
    client = TestClient(app)
    session = client.post("/api/v1/sessions", json={"title": "routing"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "现在几点", "model_id": "mock"})
    assert response.json()["data"]["steps"][0]["type"] == "retrieval_skipped"
