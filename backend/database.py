"""
database.py - SQLite connection and session management.

Key ideas:
  engine       = the connection to the learning.db file
  SessionLocal = a factory that makes "sessions" (a session is one conversation with the database)
  Base         = the parent class of all table models in models.py
  get_db()     = gives each API request its own session and closes it afterwards
  init_db()    = creates the tables if they do not exist yet
"""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# learning.db is saved inside the backend folder, no matter where you start the server from
DATABASE_PATH = Path(__file__).parent / "learning.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# check_same_thread=False: FastAPI may use different threads for one request
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def turn_on_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign-key rules unless we switch them on for every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Every table model in models.py inherits from this class."""


def get_db():
    """FastAPI dependency: one session per request, always closed at the end."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables that do not exist yet. Existing tables and data are kept."""
    import models  # noqa: F401  (importing registers the tables with Base)

    Base.metadata.create_all(bind=engine)
