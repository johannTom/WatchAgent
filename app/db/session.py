from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL
from app.db.models import Base


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    db_path = Path(database_url.removeprefix("sqlite:///"))
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(DATABASE_URL)

engine_kwargs: dict = {}
connect_args: dict = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if DATABASE_URL.endswith(":memory:"):
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
