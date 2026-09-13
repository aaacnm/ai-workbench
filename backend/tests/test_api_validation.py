from fastapi.testclient import TestClient

from app.main import app


def test_model_provider_is_validated():
    response = TestClient(app).post("/api/v1/config/model", json={"provider": "unknown", "model_name": "x"})
    assert response.status_code == 422


def test_document_content_has_max_length():
    response = TestClient(app).post("/api/v1/documents", json={"filename": "large.txt", "content": "x" * 200001})
    assert response.status_code == 422
