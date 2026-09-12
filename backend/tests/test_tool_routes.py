from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculator_route_uses_registry():
    response = client.post("/api/v1/tools/calculator", json={"expression": "10 / 2"})
    assert response.status_code == 200
    assert response.json()["data"]["output"] == 5


def test_file_route_rejects_path_escape():
    response = client.post("/api/v1/tools/file", json={"path": "../secret.txt"})
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "FILE_TOOL_ERROR"
