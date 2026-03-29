from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_create_org(client: TestClient, admin_headers: dict):
    resp = client.post("/orgs", json={"name": "New Org", "email": "org@test.com"}, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Org"
    assert data["email"] == "org@test.com"
    assert "id" in data


def test_list_orgs(client: TestClient, admin_headers: dict):
    resp = client.get("/orgs", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_get_org(client: TestClient, admin_headers: dict, org_id: str):
    resp = client.get(f"/orgs/{org_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == org_id


def test_update_org(client: TestClient, admin_headers: dict, org_id: str):
    resp = client.put(f"/orgs/{org_id}", json={"name": "Updated Org"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Org"


def test_create_site(client: TestClient, admin_headers: dict, org_id: str):
    resp = client.post(
        f"/orgs/{org_id}/sites",
        json={"name": "Test Site", "timezone": "Europe/London"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Site"
    assert data["org_id"] == org_id


def test_create_unit(client: TestClient, admin_headers: dict, org_id: str):
    # Create site first
    site_resp = client.post(
        f"/orgs/{org_id}/sites",
        json={"name": "Site for Unit", "timezone": "Europe/London"},
        headers=admin_headers,
    )
    site_id = site_resp.json()["id"]

    resp = client.post(
        f"/sites/{site_id}/units",
        json={"name": "Test Unit", "description": "A test unit"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Unit"
    assert data["site_id"] == site_id


def test_register_device(client: TestClient, admin_headers: dict, org_id: str):
    site_resp = client.post(
        f"/orgs/{org_id}/sites",
        json={"name": "Device Site"},
        headers=admin_headers,
    )
    site_id = site_resp.json()["id"]
    resp = client.post(
        f"/sites/{site_id}/devices",
        json={"device_fingerprint": "abc123", "device_name": "iPad 1"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["device_fingerprint"] == "abc123"


def test_access_policy(client: TestClient, admin_headers: dict, org_id: str):
    site_resp = client.post(
        f"/orgs/{org_id}/sites",
        json={"name": "Policy Site"},
        headers=admin_headers,
    )
    site_id = site_resp.json()["id"]
    resp = client.post(
        f"/sites/{site_id}/access-policy",
        json={"require_ip_allowlist": False, "require_approved_device": False},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["site_id"] == site_id


def test_get_nonexistent_org(client: TestClient, admin_headers: dict):
    resp = client.get("/orgs/nonexistent-id", headers=admin_headers)
    assert resp.status_code == 404
