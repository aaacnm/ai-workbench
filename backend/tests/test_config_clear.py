from fastapi.testclient import TestClient

from app.main import app
from app.db.config_store import StoredModelConfig, save_config
from app.db.database import SessionLocal


def test_clear_model_config():
    response = TestClient(app).delete("/api/v1/config/model")
    assert response.json()["data"]["cleared"] is True
    assert response.json()["data"]["provider"] == "mock"


def test_clear_only_removes_current_profile(monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("CONFIG_ENCRYPTION_KEY", Fernet.generate_key().decode())
    save_config({"provider": "openai-compatible", "model_name": "one", "base_url": "https://one", "api_key": "key-one", "temperature": 0.2, "max_tokens": 100, "timeout_seconds": 10})
    save_config({"provider": "deepseek", "model_name": "two", "base_url": "https://two", "api_key": "key-two", "temperature": 0.2, "max_tokens": 100, "timeout_seconds": 10})
    monkeypatch.setattr("app.main.runtime_model_state.provider", "openai-compatible")
    monkeypatch.setattr("app.main.runtime_model_state.model_name", "one")
    TestClient(app).delete("/api/v1/config/model")
    with SessionLocal() as db:
        rows = db.query(StoredModelConfig).all()
        assert [(row.provider, row.model_name) for row in rows] == [("deepseek", "two")]
