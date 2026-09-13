from fastapi.testclient import TestClient

from app.main import app


def test_arithmetic_uses_calculator_even_with_configured_model():
    client = TestClient(app)
    session = client.post("/api/v1/sessions", json={"title": "intent"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "1 + 1", "model_id": "mock"})
    data = response.json()["data"]
    assert any(step.get("tool_name") == "calculator" for step in data["steps"])
