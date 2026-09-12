from fastapi.testclient import TestClient

from app.main import app
from cryptography.fernet import Fernet


client = TestClient(app)


def test_model_config_does_not_return_secret(monkeypatch):
    monkeypatch.setenv("CONFIG_ENCRYPTION_KEY", Fernet.generate_key().decode())
    response = client.post("/api/v1/config/model", json={"provider": "deepseek", "model_name": "deepseek-chat", "api_key": "secret", "temperature": 0.4, "max_tokens": 512, "timeout_seconds": 20})
    body = response.json()["data"]
    assert body["api_key_configured"] is True
    assert "api_key" not in body


def test_model_config_summary_is_safe():
    body = client.get("/api/v1/config/model").json()["data"]
    assert "api_key" not in body
    assert "api_key_configured" in body


def test_model_config_refreshes_runtime_model():
    response = client.post("/api/v1/config/model", json={"provider": "mock", "model_name": "mock"})
    assert response.json()["success"] is True
    models = client.get("/api/v1/models").json()["data"]
    assert models[0]["provider"] == "mock"


def test_config_requires_encryption_key(monkeypatch):
    monkeypatch.delenv("CONFIG_ENCRYPTION_KEY", raising=False)
    response = client.post("/api/v1/config/model", json={"provider": "deepseek", "model_name": "deepseek-chat", "api_key": "secret"})
    assert response.json()["error"]["code"] == "CONFIG_ENCRYPTION_ERROR"
