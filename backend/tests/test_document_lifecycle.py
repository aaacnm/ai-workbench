from fastapi.testclient import TestClient
from app.main import app


def test_duplicate_upload_and_delete():
    client = TestClient(app)
    payload = {"filename": "profile.md", "content": "我叫彭健豪。"}
    first = client.post("/api/v1/documents", json=payload).json()["data"]
    second = client.post("/api/v1/documents", json=payload).json()["data"]
    assert first["id"] == second["id"]
    deleted = client.delete(f"/api/v1/documents/{first['id']}")
    assert deleted.json()["data"]["deleted"] is True

def test_raw_text_file_upload():
    response = TestClient(app).post("/api/v1/documents/upload?filename=notes.md", content="hello knowledge".encode("utf-8"))
    assert response.json()["data"]["filename"] == "notes.md"
