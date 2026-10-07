"""Shared pytest fixtures (test database, session, client)."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI TestClient for route tests.

    Returns:
        A TestClient wrapping the FastAPI app instance.
    """
    return TestClient(app)


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an SQLAlchemy session against a fresh in-memory SQLite database.

    Yields:
        An open session with all tables created, torn down after the test.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()
