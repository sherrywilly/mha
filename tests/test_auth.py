from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_login(client: TestClient, admin_user_data: dict):
    resp = client.post(
        "/auth/token",
        data={"username": admin_user_data["email"], "password": admin_user_data["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, admin_user_data: dict):
    resp = client.post(
        "/auth/token",
        data={"username": admin_user_data["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_refresh_token(client: TestClient, admin_user_data: dict):
    login_resp = client.post(
        "/auth/token",
        data={"username": admin_user_data["email"], "password": admin_user_data["password"]},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_get_current_user(client: TestClient, admin_headers: dict):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "ADMIN"


def test_logout(client: TestClient, admin_headers: dict):
    resp = client.post("/auth/logout", headers=admin_headers)
    assert resp.status_code == 200


def test_unauthorized_access(client: TestClient):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
