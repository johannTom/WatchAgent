# Name: Johan Tom Chacko
# Date: 2026-05-27
# What this file does: pytest setup — fresh in-memory db for each test and a TestClient for the API.

import os

# Set this before importing the app so tests never touch my real weather.db file
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENABLE_POLLER"] = "false"

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
