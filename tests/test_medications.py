from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def setup_data(client: TestClient, admin_headers: dict, org_id: str):
    """Create site, unit, resident, drug for medication tests."""
    site_resp = client.post(
        f"/orgs/{org_id}/sites",
        json={"name": "Med Site"},
        headers=admin_headers,
    )
    site_id = site_resp.json()["id"]

    unit_resp = client.post(
        f"/sites/{site_id}/units",
        json={"name": "Med Unit"},
        headers=admin_headers,
    )
    unit_id = unit_resp.json()["id"]

    resident_resp = client.post(
        "/residents",
        json={
            "unit_id": unit_id,
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "1940-01-01",
        },
        headers=admin_headers,
    )
    resident_id = resident_resp.json()["id"]

    drug_resp = client.post(
        "/drugs",
        json={"name": "Paracetamol", "form": "TABLET", "strength": "500mg"},
        headers=admin_headers,
    )
    drug_id = drug_resp.json()["id"]

    return {
        "site_id": site_id,
        "unit_id": unit_id,
        "resident_id": resident_id,
        "drug_id": drug_id,
    }


def test_create_drug(client: TestClient, admin_headers: dict):
    resp = client.post(
        "/drugs",
        json={"name": "Ibuprofen", "form": "TABLET", "strength": "200mg", "is_controlled": False},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Ibuprofen"


def test_list_drugs(client: TestClient, admin_headers: dict):
    resp = client.get("/drugs", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_medication_order(client: TestClient, admin_headers: dict, setup_data: dict):
    event_id = str(uuid.uuid4())
    resp = client.post(
        "/medication-orders",
        json={
            "resident_id": setup_data["resident_id"],
            "drug_id": setup_data["drug_id"],
            "prescribed_by": "Dr Smith",
            "dose": "500",
            "dose_unit": "mg",
            "route": "ORAL",
            "frequency_type": "DAILY_TIMES",
            "frequency_times": ["08:00", "20:00"],
            "start_date": str(date.today()),
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["drug_id"] == setup_data["drug_id"]
    assert data["client_event_id"] == event_id


def test_medication_order_idempotency(client: TestClient, admin_headers: dict, setup_data: dict):
    event_id = str(uuid.uuid4())
    payload = {
        "resident_id": setup_data["resident_id"],
        "drug_id": setup_data["drug_id"],
        "prescribed_by": "Dr Smith",
        "dose": "250",
        "dose_unit": "mg",
        "route": "ORAL",
        "frequency_type": "DAILY_TIMES",
        "frequency_times": ["12:00"],
        "start_date": str(date.today()),
        "client_event_id": event_id,
    }
    resp1 = client.post("/medication-orders", json=payload, headers=admin_headers)
    resp2 = client.post("/medication-orders", json=payload, headers=admin_headers)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


def test_generate_dose_due(client: TestClient, admin_headers: dict, setup_data: dict):
    event_id = str(uuid.uuid4())
    order_resp = client.post(
        "/medication-orders",
        json={
            "resident_id": setup_data["resident_id"],
            "drug_id": setup_data["drug_id"],
            "prescribed_by": "Dr Jones",
            "dose": "500",
            "dose_unit": "mg",
            "route": "ORAL",
            "frequency_type": "DAILY_TIMES",
            "frequency_times": ["08:00"],
            "start_date": "2025-01-01",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    order_id = order_resp.json()["id"]

    resp = client.post(
        "/dose-due/generate",
        json={"order_id": order_id, "date_from": "2025-01-01", "date_to": "2025-01-03"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    doses = resp.json()
    assert len(doses) == 3  # 3 days, 1 dose per day


def test_generate_dose_due_idempotent(client: TestClient, admin_headers: dict, setup_data: dict):
    event_id = str(uuid.uuid4())
    order_resp = client.post(
        "/medication-orders",
        json={
            "resident_id": setup_data["resident_id"],
            "drug_id": setup_data["drug_id"],
            "prescribed_by": "Dr Jones",
            "dose": "500",
            "dose_unit": "mg",
            "route": "ORAL",
            "frequency_type": "DAILY_TIMES",
            "frequency_times": ["08:00"],
            "start_date": "2025-02-01",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    order_id = order_resp.json()["id"]

    resp1 = client.post(
        "/dose-due/generate",
        json={"order_id": order_id, "date_from": "2025-02-01", "date_to": "2025-02-02"},
        headers=admin_headers,
    )
    resp2 = client.post(
        "/dose-due/generate",
        json={"order_id": order_id, "date_from": "2025-02-01", "date_to": "2025-02-02"},
        headers=admin_headers,
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # Second call returns 0 new doses because all dose_keys already exist
    assert len(resp2.json()) == 0


def test_record_administration(client: TestClient, admin_headers: dict, setup_data: dict):
    event_id = str(uuid.uuid4())
    order_event_id = str(uuid.uuid4())
    order_resp = client.post(
        "/medication-orders",
        json={
            "resident_id": setup_data["resident_id"],
            "drug_id": setup_data["drug_id"],
            "prescribed_by": "Dr Test",
            "dose": "500",
            "dose_unit": "mg",
            "route": "ORAL",
            "frequency_type": "PRN",
            "start_date": str(date.today()),
            "client_event_id": order_event_id,
        },
        headers=admin_headers,
    )
    order_id = order_resp.json()["id"]

    resp = client.post(
        "/administrations",
        json={
            "order_id": order_id,
            "resident_id": setup_data["resident_id"],
            "administered_at": "2025-01-01T08:00:00",
            "dose_given": "500",
            "dose_unit": "mg",
            "route_used": "ORAL",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["order_id"] == order_id
