from fastapi.testclient import TestClient

from app.main import app


def test_document_upload_and_detail():
    client = TestClient(app)
    response = client.post("/api/v1/documents", json={"filename": "notes.md", "content": "第一段\n第二段"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["filename"] == "notes.md"
    detail = client.get(f"/api/v1/documents/{data['id']}")
    assert detail.json()["data"]["chunks"][0]["metadata"]["source"] == "notes.md"
