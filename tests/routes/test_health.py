"""Tests for the /health route."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """Verify /health responds with 200 and the expected status payload."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "broken"}
