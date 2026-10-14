"""Shared pytest fixtures (test database, session, client)."""

import httpx2

# Must run before anything imports httpx, so the imports below stay after it.
# FastAPI's TestClient and respx (in the test modules) import `httpx`; this makes
# it resolve to httpx2. respx's pytest plugin is disabled in pyproject.toml
# because pytest would load it before this file. Tests that use respx should
# therefore import `httpx`, not `httpx2`: it is the same module at runtime, and
# respx's type hints expect `httpx` types, which mypy can only match that way.
httpx2.alias_httpx()

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable SQLite foreign key enforcement on each new connection."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()
