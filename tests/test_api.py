"""Integration tests for the REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.models import CareHome, Drug, User, UserRole


def _seed_care_home(db: Session) -> str:
    """Create a care home and return its ID as a plain string."""
    home = CareHome(name="Sunrise Care Home", bed_count=50, tier=2)
    db.add(home)
    db.commit()
    home_id: str = home.id
    return home_id


def _seed_user(db: Session, care_home_id: str, role: UserRole, email: str) -> None:
    user = User(
        care_home_id=care_home_id,
        email=email,
        hashed_password=get_password_hash("Password123!"),
        full_name="Test User",
        role=role,
    )
    db.add(user)
    db.commit()


def _get_token(client: TestClient, email: str, care_home_id: str) -> str:
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": "Password123!", "care_home_id": care_home_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestAuth:
    def test_login_success(self, client: TestClient):
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        home_id = _seed_care_home(db)
        _seed_user(db, home_id, UserRole.nurse, "nurse@test.com")
        db.close()

        resp = client.post(
            "/auth/login",
            json={
                "email": "nurse@test.com",
                "password": "Password123!",
                "care_home_id": home_id,
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client: TestClient):
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        home_id = _seed_care_home(db)
        _seed_user(db, home_id, UserRole.nurse, "nurse2@test.com")
        db.close()

        resp = client.post(
            "/auth/login",
            json={
                "email": "nurse2@test.com",
                "password": "WrongPass!",
                "care_home_id": home_id,
            },
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Residents
# ---------------------------------------------------------------------------


class TestResidents:
    def _setup(self, client: TestClient):
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        home_id = _seed_care_home(db)
        _seed_user(db, home_id, UserRole.nurse, "nurse_res@test.com")
        db.close()
        token = _get_token(client, "nurse_res@test.com", home_id)
        return token, home_id

    def test_create_resident(self, client: TestClient):
        token, _ = self._setup(client)
        resp = client.post(
            "/residents/",
            json={"full_name": "Alice Smith", "room_number": "12A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["full_name"] == "Alice Smith"

    def test_list_residents(self, client: TestClient):
        token, _ = self._setup(client)
        client.post(
            "/residents/",
            json={"full_name": "Bob Jones"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            "/residents/", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_family_cannot_create_resident(self, client: TestClient):
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        home_id = _seed_care_home(db)
        _seed_user(db, home_id, UserRole.family, "family_res@test.com")
        db.close()
        token = _get_token(client, "family_res@test.com", home_id)
        resp = client.post(
            "/residents/",
            json={"full_name": "Charlie Brown"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Lead CRM
# ---------------------------------------------------------------------------


class TestLeads:
    def _setup(self, client: TestClient):
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        home_id = _seed_care_home(db)
        _seed_user(db, home_id, UserRole.admin, "admin_leads@test.com")
        db.close()
        token = _get_token(client, "admin_leads@test.com", home_id)
        return token, home_id

    def test_create_lead_scores_automatically(self, client: TestClient):
        token, _ = self._setup(client)
        resp = client.post(
            "/leads/",
            json={
                "enquirer_name": "Jane Doe",
                "enquirer_email": "jane@example.com",
                "source": "hospital_discharge",
                "care_needs": "dementia care required",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["urgency_score"] > 0
        assert data["status"] == "new"

    def test_leads_sorted_by_urgency(self, client: TestClient):
        token, _ = self._setup(client)
        client.post(
            "/leads/",
            json={"enquirer_name": "Low Priority", "source": "website"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/leads/",
            json={"enquirer_name": "High Priority", "source": "hospital_discharge"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get("/leads/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        scores = [l["urgency_score"] for l in resp.json()]
        assert scores == sorted(scores, reverse=True)

    def test_update_lead_status(self, client: TestClient):
        token, _ = self._setup(client)
        create_resp = client.post(
            "/leads/",
            json={"enquirer_name": "Status Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        lead_id = create_resp.json()["id"]
        resp = client.patch(
            f"/leads/{lead_id}/status",
            json={"new_status": "contacted", "notes": "Called back"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "contacted"
