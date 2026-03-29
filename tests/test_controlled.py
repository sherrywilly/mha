from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def cd_setup(client: TestClient, admin_headers: dict, org_id: str):
    site_resp = client.post(f"/orgs/{org_id}/sites", json={"name": "CD Site"}, headers=admin_headers)
    site_id = site_resp.json()["id"]

    unit_resp = client.post(f"/sites/{site_id}/units", json={"name": "CD Unit"}, headers=admin_headers)
    unit_id = unit_resp.json()["id"]

    # Assign CD permission to admin
    from tests.conftest import TestingSessionLocal
    from app.models.org import UnitAssignment
    db = TestingSessionLocal()
    try:
        from app.models.org import User
        user = db.query(User).filter_by(email="admin@test.com").first()
        assignment = UnitAssignment(user_id=user.id, unit_id=unit_id, can_administer_cd=True)
        db.add(assignment)
        db.commit()
    finally:
        db.close()

    drug_resp = client.post(
        "/drugs",
        json={"name": "Morphine", "form": "LIQUID", "is_controlled": True, "controlled_schedule": 2},
        headers=admin_headers,
    )
    drug_id = drug_resp.json()["id"]

    return {"site_id": site_id, "unit_id": unit_id, "drug_id": drug_id}


def test_create_cd_transaction(client: TestClient, admin_headers: dict, cd_setup: dict):
    event_id = str(uuid.uuid4())
    resp = client.post(
        "/cd/transactions",
        json={
            "drug_id": cd_setup["drug_id"],
            "site_id": cd_setup["site_id"],
            "tx_type": "RECEIVED",
            "quantity": 10.0,
            "unit": "ml",
            "performed_at": "2025-01-01T08:00:00",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tx_type"] == "RECEIVED"
    assert data["quantity"] == 10.0
    assert data["witness_status"] == "PENDING"


def test_cd_transaction_idempotency(client: TestClient, admin_headers: dict, cd_setup: dict):
    event_id = str(uuid.uuid4())
    payload = {
        "drug_id": cd_setup["drug_id"],
        "site_id": cd_setup["site_id"],
        "tx_type": "RECEIVED",
        "quantity": 5.0,
        "unit": "ml",
        "performed_at": "2025-01-01T09:00:00",
        "client_event_id": event_id,
    }
    resp1 = client.post("/cd/transactions", json=payload, headers=admin_headers)
    resp2 = client.post("/cd/transactions", json=payload, headers=admin_headers)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


def test_witness_cd_transaction(client: TestClient, admin_headers: dict, cd_setup: dict):
    # Create a second user for witnessing
    from passlib.context import CryptContext
    from tests.conftest import TestingSessionLocal
    from app.models.org import User, UnitAssignment
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter_by(email="admin@test.com").first()
        witness_user = User(
            org_id=admin.org_id,
            email="witness@test.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="Witness User",
            role="NURSE",
        )
        db.add(witness_user)
        db.flush()
        assignment = UnitAssignment(user_id=witness_user.id, unit_id=cd_setup["unit_id"], can_administer_cd=True)
        db.add(assignment)
        db.commit()
        witness_id = witness_user.id
    finally:
        db.close()

    # Create a transaction to witness
    event_id = str(uuid.uuid4())
    tx_resp = client.post(
        "/cd/transactions",
        json={
            "drug_id": cd_setup["drug_id"],
            "site_id": cd_setup["site_id"],
            "tx_type": "RECEIVED",
            "quantity": 3.0,
            "unit": "ml",
            "performed_at": "2025-01-01T10:00:00",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    tx_id = tx_resp.json()["id"]

    # Witness it
    resp = client.post(
        f"/cd/transactions/{tx_id}/witness",
        json={"witnessed_by": witness_id, "witnessed_at": "2025-01-01T10:05:00"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["witness_status"] == "COMPLETE"
    assert data["witnessed_by"] == witness_id


def test_witness_same_person_fails(client: TestClient, admin_headers: dict, cd_setup: dict):
    from tests.conftest import TestingSessionLocal
    from app.models.org import User
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter_by(email="admin@test.com").first()
        admin_id = admin.id
    finally:
        db.close()

    event_id = str(uuid.uuid4())
    tx_resp = client.post(
        "/cd/transactions",
        json={
            "drug_id": cd_setup["drug_id"],
            "site_id": cd_setup["site_id"],
            "tx_type": "RECEIVED",
            "quantity": 2.0,
            "unit": "ml",
            "performed_at": "2025-01-01T11:00:00",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    tx_id = tx_resp.json()["id"]

    # Try to witness with same user
    resp = client.post(
        f"/cd/transactions/{tx_id}/witness",
        json={"witnessed_by": admin_id, "witnessed_at": "2025-01-01T11:05:00"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_pending_witness_list(client: TestClient, admin_headers: dict, cd_setup: dict):
    resp = client.get(f"/cd/pending-witness?site_id={cd_setup['site_id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_cd_balance(client: TestClient, admin_headers: dict, cd_setup: dict):
    resp = client.get(
        f"/cd/balance?site_id={cd_setup['site_id']}&drug_id={cd_setup['drug_id']}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    if resp.json():
        assert resp.json()[0]["drug_id"] == cd_setup["drug_id"]
