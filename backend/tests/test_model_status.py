from fastapi.testclient import TestClient

from app.main import app


def test_mock_model_status():
    response = TestClient(app).get("/api/v1/models/mock/status")
    assert response.json()["data"]["configured"] is True
    assert response.json()["data"]["reachable"] is None


def test_unknown_model_status():
    response = TestClient(app).get("/api/v1/models/missing/status")
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"
