"""Shared pytest fixtures for the Kharchify test suite."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


def make_expense(**overrides) -> dict:
    """Return a valid expense payload dict. Accepts keyword overrides."""
    base = {
        "title": "Test Lunch",
        "amount": 50.00,
        "category_id": 1,          # Food — always seeded
        "expense_date": "2026-01-15",  # Fixed past date; never becomes "future"
        "note": None,
    }
    base.update(overrides)
    return base


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient backed by a fresh temporary SQLite database.

    The lifespan runs (via context-manager usage of TestClient), so
    init_db is called and the schema + seed categories are created before
    any test request is made.
    """
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "database_path", db_file)

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client) -> dict:
    """Register alice, log in, and return Bearer auth headers."""
    client.post("/api/auth/register", json={"username": "alice", "password": "Secret123"})
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "Secret123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_user_headers(client) -> dict:
    """Register bob, log in, and return Bearer auth headers."""
    client.post("/api/auth/register", json={"username": "bob", "password": "Secret123"})
    resp = client.post("/api/auth/login", json={"username": "bob", "password": "Secret123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
