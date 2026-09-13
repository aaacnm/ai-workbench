from fastapi.testclient import TestClient
from app.main import app

def test_unknown_session_is_not_created():
    response = TestClient(app).post("/api/v1/sessions/missing/messages", json={"content": "hello", "model_id": "mock"})
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
