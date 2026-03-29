import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from app.database import get_db
from app.core.security import hash_password
from main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import app.models
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def admin_role(db, setup_db):
    from app.models.user import Role
    role = Role(id=str(uuid4()), name="admin", permissions=["manage_users", "manage_org"])
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@pytest.fixture(scope="session")
def admin_user(db, admin_role):
    from app.models.user import User
    from app.models.organisation import Organisation
    org = Organisation(id=str(uuid4()), name="Test Org", is_active=True)
    db.add(org)
    db.commit()
    user = User(
        id=str(uuid4()),
        email="admin@test.com",
        hashed_password=hash_password("adminpass"),
        full_name="Admin User",
        role_id=admin_role.id,
        organisation_id=org.id,
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="session")
def client(admin_user):
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def admin_token(client):
    resp = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "adminpass"})
    assert resp.status_code == 200
    return resp.json()["access_token"]
