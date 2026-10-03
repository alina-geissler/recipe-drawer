"""Tests for page rendering routes."""

from fastapi.testclient import TestClient


def test_start_page_returns_html(client: TestClient) -> None:
    """Verify / responds with 200 and renders the start page template."""
    response = client.get("/")

    assert response.status_code == 200
    assert "Willkommen" in response.text
