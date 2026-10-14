"""
conftest.py - Shared test setup (pytest loads this file automatically).

Every test gets a fresh, empty, temporary database that already contains the
starter careers and skills. Your real learning.db is never touched.
"""
import sys
from pathlib import Path

# Lets the tests import main.py, services/, etc. from the backend folder
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  (registers the tables)
from database import Base, get_db
from main import app
from seed import seed_database


@pytest.fixture()
def session_factory():
    """A brand-new in-memory SQLite database with the starter data loaded."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keeps one shared in-memory database
    )

    @event.listens_for(engine, "connect")
    def turn_on_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with factory() as db:
        seed_database(db)

    yield factory
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    """A test client whose API uses the temporary database."""

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # not used as "with": the startup code that touches learning.db is skipped
    app.dependency_overrides.clear()
