from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_message_rejects_unknown_model():
    response = client.post("/api/v1/sessions/model-selection/messages", json={"content": "hello", "model_id": "missing"})
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"


def test_message_uses_default_mock_model():
    response = client.post("/api/v1/sessions/model-selection/messages", json={"content": "请计算 2 + 2"})
    assert response.json()["success"] is True
    assert response.json()["data"]["model"] == "mock"
