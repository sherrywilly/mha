def test_login_returns_token(client):
    resp = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "adminpass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_protected_without_token_returns_401(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

def test_wrong_password_returns_401(client):
    resp = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "wrongpass"})
    assert resp.status_code == 401

def test_create_user_requires_admin(client, admin_token, admin_role):
    resp = client.post(
        "/api/v1/auth/users",
        json={"email": "nurse@test.com", "password": "nursepass", "full_name": "Test Nurse", "role_id": admin_role.id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code in (200, 201)
