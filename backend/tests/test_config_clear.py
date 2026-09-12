from fastapi.testclient import TestClient

from app.main import app


def test_clear_model_config():
    response = TestClient(app).delete("/api/v1/config/model")
    assert response.json()["data"]["cleared"] is True
    assert response.json()["data"]["provider"] == "mock"
