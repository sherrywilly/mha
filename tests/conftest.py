"""
Unit tests for SafeCare eMAR & Lead Engine.

These tests use pytest and do NOT require a live PostgreSQL database.
Services (Vitals Bridge, Lead Scoring) are tested in pure Python.
FastAPI routes are tested via TestClient with a file-based SQLite test database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# In-memory SQLite test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
