"""Database engine, session factory and the FastAPI session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key enforcement on each new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session]:
    """Yield a database session for use as a FastAPI dependency.

    The session is closed after the request completes, regardless of
    whether an exception occurred. Callers are responsible for committing;
    this dependency never commits on their behalf.

    Yields:
        An active SQLAlchemy session bound to the configured database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
