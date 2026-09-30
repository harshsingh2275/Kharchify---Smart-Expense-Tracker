"""Tests for authentication endpoints: register, login, me."""

import time

import jwt
import pytest

from app.config import settings
from app.database import get_connection


# ─── Register ──────────────────────────────────────────────────────────────


def test_register_success_returns_201_and_user_shape(client):
    resp = client.post("/api/auth/register", json={"username": "charlie", "password": "Secret123"})
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["username"] == "charlie"
    assert "created_at" in body


def test_register_response_has_no_password_fields(client):
    resp = client.post("/api/auth/register", json={"username": "dave", "password": "Secret123"})
    assert resp.status_code == 201
    body = resp.json()
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_returns_409(client, auth_headers):
    # alice already exists (created by auth_headers fixture)
    resp = client.post("/api/auth/register", json={"username": "alice", "password": "Secret123"})
    assert resp.status_code == 409
    assert resp.json() == {"detail": "Username already taken"}


def test_register_duplicate_different_case_returns_409(client, auth_headers):
    # "Alice" vs "alice" must also conflict
    resp = client.post("/api/auth/register", json={"username": "Alice", "password": "Secret123"})
    assert resp.status_code == 409
    assert resp.json() == {"detail": "Username already taken"}


def test_register_password_stored_as_bcrypt_hash(client, tmp_path):
    """Password in DB must be a bcrypt hash, not plaintext."""
    resp = client.post("/api/auth/register", json={"username": "hashcheck", "password": "MySecret99"})
    assert resp.status_code == 201
    conn = get_connection(settings.database_path)
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", ("hashcheck",)
    ).fetchone()
    conn.close()
    assert row is not None
    hashed = row["password_hash"]
    assert hashed.startswith("$2"), f"Expected bcrypt hash, got: {hashed!r}"
    assert hashed != "MySecret99"


# ─── Login ─────────────────────────────────────────────────────────────────


def test_login_success_returns_200_and_token(client, auth_headers):
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "Secret123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401_generic_message(client, auth_headers):
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "WrongPass"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Incorrect username or password"}


def test_login_unknown_user_returns_401_same_message(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "Secret123"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Incorrect username or password"}


def test_login_wrong_password_and_unknown_user_have_identical_message(client, auth_headers):
    bad_pass = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    no_user = client.post("/api/auth/login", json={"username": "ghost", "password": "Secret123"})
    assert bad_pass.json()["detail"] == no_user.json()["detail"]


# ─── Me ────────────────────────────────────────────────────────────────────


def test_me_with_valid_token_returns_200_and_correct_username(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_me_without_token_returns_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_without_token_has_www_authenticate_bearer_header(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"


# ─── Protected endpoints require auth ───────────────────────────────────────


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/categories"),
    ("GET", "/api/expenses"),
    ("POST", "/api/expenses"),
    ("GET", "/api/summary"),
])
def test_protected_endpoint_without_token_returns_401(client, method, path):
    resp = client.request(method, path)
    assert resp.status_code == 401


# ─── Malformed / expired / unknown-user tokens ─────────────────────────────


def test_malformed_token_returns_401(client):
    headers = {"Authorization": "Bearer abc.bad.token"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401


def test_expired_token_returns_401(client, auth_headers):
    # Build a token that expired one second ago
    payload = {"sub": "1", "exp": int(time.time()) - 1}
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_token_for_nonexistent_user_returns_401(client):
    # Build a valid, unexpired token for a user id that will never exist
    payload = {"sub": "999999", "exp": int(time.time()) + 3600}
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
