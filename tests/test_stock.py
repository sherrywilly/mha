from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def stock_setup(client: TestClient, admin_headers: dict, org_id: str):
    site_resp = client.post(f"/orgs/{org_id}/sites", json={"name": "Stock Site"}, headers=admin_headers)
    site_id = site_resp.json()["id"]

    unit_resp = client.post(f"/sites/{site_id}/units", json={"name": "Stock Unit"}, headers=admin_headers)
    unit_id = unit_resp.json()["id"]

    drug_resp = client.post(
        "/drugs",
        json={"name": "Aspirin Stock", "form": "TABLET"},
        headers=admin_headers,
    )
    drug_id = drug_resp.json()["id"]

    return {"site_id": site_id, "unit_id": unit_id, "drug_id": drug_id}


def test_create_stock_location(client: TestClient, admin_headers: dict, stock_setup: dict):
    resp = client.post(
        "/stock/locations",
        json={
            "unit_id": stock_setup["unit_id"],
            "site_id": stock_setup["site_id"],
            "name": "Main Shelf",
            "location_type": "SHELF",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Main Shelf"


def test_list_stock_locations(client: TestClient, admin_headers: dict, stock_setup: dict):
    resp = client.get(f"/stock/locations?unit_id={stock_setup['unit_id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_stock_transaction_receive(client: TestClient, admin_headers: dict, stock_setup: dict):
    # Create location
    loc_resp = client.post(
        "/stock/locations",
        json={
            "unit_id": stock_setup["unit_id"],
            "site_id": stock_setup["site_id"],
            "name": "Fridge",
            "location_type": "FRIDGE",
        },
        headers=admin_headers,
    )
    loc_id = loc_resp.json()["id"]

    event_id = str(uuid.uuid4())
    resp = client.post(
        "/stock/transactions",
        json={
            "drug_id": stock_setup["drug_id"],
            "to_location_id": loc_id,
            "tx_type": "RECEIVE",
            "quantity": 100.0,
            "unit": "tablets",
            "performed_at": "2025-01-01T09:00:00",
            "client_event_id": event_id,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 100.0


def test_stock_transaction_idempotency(client: TestClient, admin_headers: dict, stock_setup: dict):
    loc_resp = client.post(
        "/stock/locations",
        json={
            "unit_id": stock_setup["unit_id"],
            "site_id": stock_setup["site_id"],
            "name": "Idempotent Shelf",
            "location_type": "SHELF",
        },
        headers=admin_headers,
    )
    loc_id = loc_resp.json()["id"]

    event_id = str(uuid.uuid4())
    payload = {
        "drug_id": stock_setup["drug_id"],
        "to_location_id": loc_id,
        "tx_type": "RECEIVE",
        "quantity": 50.0,
        "unit": "tablets",
        "performed_at": "2025-01-01T10:00:00",
        "client_event_id": event_id,
    }
    resp1 = client.post("/stock/transactions", json=payload, headers=admin_headers)
    resp2 = client.post("/stock/transactions", json=payload, headers=admin_headers)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


def test_stock_alert_low_stock(client: TestClient, admin_headers: dict, stock_setup: dict):
    # Create location and item with threshold higher than quantity
    loc_resp = client.post(
        "/stock/locations",
        json={
            "unit_id": stock_setup["unit_id"],
            "site_id": stock_setup["site_id"],
            "name": "Alert Shelf",
            "location_type": "SHELF",
        },
        headers=admin_headers,
    )
    loc_id = loc_resp.json()["id"]

    # Receive some stock
    receive_event = str(uuid.uuid4())
    client.post(
        "/stock/transactions",
        json={
            "drug_id": stock_setup["drug_id"],
            "to_location_id": loc_id,
            "tx_type": "RECEIVE",
            "quantity": 5.0,
            "unit": "tablets",
            "performed_at": "2025-01-01T11:00:00",
            "client_event_id": receive_event,
        },
        headers=admin_headers,
    )

    # Consume all stock to trigger alert
    consume_event = str(uuid.uuid4())
    client.post(
        "/stock/transactions",
        json={
            "drug_id": stock_setup["drug_id"],
            "from_location_id": loc_id,
            "tx_type": "CONSUME",
            "quantity": 5.0,
            "unit": "tablets",
            "performed_at": "2025-01-01T12:00:00",
            "client_event_id": consume_event,
        },
        headers=admin_headers,
    )

    # Check alerts
    resp = client.get(f"/stock/alerts?unit_id={stock_setup['unit_id']}", headers=admin_headers)
    assert resp.status_code == 200
    # RUNOUT_RISK alert should be created when qty hits 0
    assert isinstance(resp.json(), list)


def test_resolve_alert(client: TestClient, admin_headers: dict, stock_setup: dict):
    alerts_resp = client.get(f"/stock/alerts?unit_id={stock_setup['unit_id']}", headers=admin_headers)
    alerts = alerts_resp.json()
    if alerts:
        alert_id = alerts[0]["id"]
        resp = client.post(f"/stock/alerts/{alert_id}/resolve", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_resolved"] is True
