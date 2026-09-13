from fastapi.testclient import TestClient

from app.main import app


class RecordingModel:
    def __init__(self):
        self.called = False

    def chat(self, messages, tools=None):
        from app.models.base import ModelResponse
        self.called = True
        return ModelResponse("模型已根据工具结果整理回答", [])


def test_configured_model_is_invoked_for_time_intent(monkeypatch):
    recorder = RecordingModel()
    monkeypatch.setattr("app.main.model_registry.get", lambda _model_id: type("Selected", (), {"config": type("Config", (), {"provider": "openai-compatible", "id": "fake"})(), "model": recorder})())
    client = TestClient(app)
    session = client.post("/api/v1/sessions", json={"title": "model"}).json()["data"]
    response = client.post(f"/api/v1/sessions/{session['id']}/messages", json={"content": "现在几点", "model_id": "fake"})
    assert response.json()["data"]["answer"] == "模型已根据工具结果整理回答"
    assert recorder.called
