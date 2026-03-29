from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base, get_db
from app.models.enums import UserRole

# Use sync SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_mha.db"

sync_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable foreign keys for SQLite
@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class _AsyncSyncSession:
    """Wraps a sync SQLAlchemy Session to make it awaitable for testing."""

    def __init__(self, session: Session):
        self._session = session

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def flush(self, *args, **kwargs):
        return self._session.flush(*args, **kwargs)

    async def commit(self, *args, **kwargs):
        return self._session.commit(*args, **kwargs)

    async def rollback(self, *args, **kwargs):
        return self._session.rollback(*args, **kwargs)

    async def get(self, model, pk, **kwargs):
        return self._session.get(model, pk)

    def add(self, instance):
        return self._session.add(instance)

    def delete(self, instance):
        return self._session.delete(instance)


def override_get_db():
    session = TestingSessionLocal()
    wrapped = _AsyncSyncSession(session)
    try:
        yield wrapped
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    # Import all models
    import app.models.org
    import app.models.resident
    import app.models.medication
    import app.models.topical
    import app.models.controlled
    import app.models.stock
    import app.models.prescription
    import app.models.error
    Base.metadata.create_all(bind=sync_engine)
    # Seed topical sites
    db = TestingSessionLocal()
    try:
        from app.models.topical import TopicalSite
        from sqlalchemy import select
        sites = [
            ("SCALP", "Scalp", "HEAD"),
            ("LEFT_ARM_UPPER", "Left Upper Arm", "LEFT_ARM"),
            ("RIGHT_ARM_UPPER", "Right Upper Arm", "RIGHT_ARM"),
            ("OTHER", "Other", "OTHER"),
        ]
        for code, label, region in sites:
            existing = db.execute(select(TopicalSite).where(TopicalSite.code == code)).scalar_one_or_none()
            if not existing:
                db.add(TopicalSite(code=code, label=label, body_region=region))
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(scope="session")
def app_instance():
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="session")
def client(app_instance):
    with TestClient(app_instance) as c:
        yield c


@pytest.fixture(scope="session")
def admin_user_data(client):
    """Create admin user and return token headers."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = TestingSessionLocal()
    try:
        from app.models.org import Organisation, User
        from sqlalchemy import select
        # Create org if not exists
        existing_user = db.execute(select(User).where(User.email == "admin@test.com")).scalar_one_or_none()
        if existing_user:
            org = db.get(Organisation, existing_user.org_id)
            return {"org_id": org.id, "user_id": existing_user.id, "email": "admin@test.com", "password": "password123"}

        org = Organisation(name="Test Org")
        db.add(org)
        db.flush()

        user = User(
            org_id=org.id,
            email="admin@test.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.refresh(org)
        return {"org_id": org.id, "user_id": user.id, "email": "admin@test.com", "password": "password123"}
    finally:
        db.close()


@pytest.fixture(scope="session")
def admin_headers(client, admin_user_data):
    resp = client.post(
        "/auth/token",
        data={"username": admin_user_data["email"], "password": admin_user_data["password"]},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def auth_headers(admin_headers):
    return admin_headers


@pytest.fixture(scope="session")
def org_id(admin_user_data):
    return admin_user_data["org_id"]

