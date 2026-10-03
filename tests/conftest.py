"""Shared pytest fixtures (test database, session, client)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI TestClient for route tests.

    Returns:
        A TestClient wrapping the FastAPI app instance.
    """
    return TestClient(app)
