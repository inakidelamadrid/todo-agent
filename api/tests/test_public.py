"""Public endpoints respond without an API key."""

from fastapi.testclient import TestClient


def test_health_returns_ok_and_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["version"], str)
    assert body["version"]


def test_ping_returns_pong(client: TestClient) -> None:
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
