import os

# Set before importing app modules so session.py picks up the test database
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENABLE_POLLER", "false")

import pytest
from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.session import SessionLocal, engine, init_db
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
