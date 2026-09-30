"""Tests for expense CRUD, filtering, pagination, and ownership isolation."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_expense


# ─── Create ────────────────────────────────────────────────────────────────


def test_create_expense_returns_201_with_all_fields(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(), headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    for key in ("id", "title", "amount", "category_id", "category_name",
                "expense_date", "note", "created_at", "updated_at"):
        assert key in body, f"Missing key: {key}"
    assert body["category_name"] == "Food"


def test_create_expense_category_name_is_populated(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(category_id=2), headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["category_name"] == "Transport"


# ─── Get one ────────────────────────────────────────────────────────────────


def test_get_expense_by_id_returns_200(client, auth_headers):
    created = client.post("/api/expenses", json=make_expense(), headers=auth_headers).json()
    resp = client.get(f"/api/expenses/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_unknown_expense_returns_404(client, auth_headers):
    resp = client.get("/api/expenses/999999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Expense not found"}


# ─── List ───────────────────────────────────────────────────────────────────


def test_list_returns_own_items_only(client, auth_headers, second_user_headers):
    client.post("/api/expenses", json=make_expense(title="Alice item"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(title="Bob item"), headers=second_user_headers)
    resp = client.get("/api/expenses", headers=auth_headers)
    assert resp.status_code == 200
    titles = [e["title"] for e in resp.json()["items"]]
    assert "Alice item" in titles
    assert "Bob item" not in titles


def test_list_envelope_shape(client, auth_headers):
    resp = client.get("/api/expenses", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total" in body
    assert "limit" in body and "offset" in body


def test_list_newest_first_by_date_then_by_id(client, auth_headers):
    """Expenses ordered: newest expense_date first, then higher id first for same date."""
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-10", title="oldest"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-20", title="newer1"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-20", title="newer2"), headers=auth_headers)

    resp = client.get("/api/expenses?limit=10", headers=auth_headers)
    items = resp.json()["items"]
    dates = [e["expense_date"] for e in items]
    # Newest date must come first
    assert dates[0] == "2026-01-20"
    assert dates[-1] == "2026-01-10"
    # Among same date, higher id first
    same_date_titles = [e["title"] for e in items if e["expense_date"] == "2026-01-20"]
    assert same_date_titles[0] == "newer2"
    assert same_date_titles[1] == "newer1"


# ─── Pagination ─────────────────────────────────────────────────────────────


def test_list_pagination_correct_slice_and_total(client, auth_headers):
    for i in range(5):
        client.post("/api/expenses", json=make_expense(title=f"item{i}"), headers=auth_headers)

    resp = client.get("/api/expenses?limit=2&offset=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 2


# ─── Filters ─────────────────────────────────────────────────────────────────


def test_list_filter_by_category_id(client, auth_headers):
    client.post("/api/expenses", json=make_expense(category_id=1, title="food"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(category_id=2, title="transport"), headers=auth_headers)
    resp = client.get("/api/expenses?category_id=1", headers=auth_headers)
    items = resp.json()["items"]
    assert all(e["category_id"] == 1 for e in items)
    titles = [e["title"] for e in items]
    assert "food" in titles
    assert "transport" not in titles


def test_list_filter_by_start_date(client, auth_headers):
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-05"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-15"), headers=auth_headers)
    resp = client.get("/api/expenses?start_date=2026-01-10", headers=auth_headers)
    items = resp.json()["items"]
    assert all(e["expense_date"] >= "2026-01-10" for e in items)


def test_list_filter_by_end_date(client, auth_headers):
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-05"), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-15"), headers=auth_headers)
    resp = client.get("/api/expenses?end_date=2026-01-10", headers=auth_headers)
    items = resp.json()["items"]
    assert all(e["expense_date"] <= "2026-01-10" for e in items)


def test_list_filter_combined(client, auth_headers):
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-05", category_id=1), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-15", category_id=2), headers=auth_headers)
    client.post("/api/expenses", json=make_expense(expense_date="2026-01-20", category_id=1), headers=auth_headers)
    resp = client.get("/api/expenses?category_id=1&start_date=2026-01-10&end_date=2026-01-25", headers=auth_headers)
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["expense_date"] == "2026-01-20"


def test_list_start_date_after_end_date_returns_400(client, auth_headers):
    resp = client.get("/api/expenses?start_date=2026-10-01&end_date=2026-09-01", headers=auth_headers)
    assert resp.status_code == 400
    assert "start_date" in resp.json()["detail"]


# ─── Update ─────────────────────────────────────────────────────────────────


def test_update_expense_returns_200_with_changed_values(client, auth_headers):
    created = client.post("/api/expenses", json=make_expense(title="Before"), headers=auth_headers).json()
    updated = make_expense(title="After", amount=200.0)
    resp = client.put(f"/api/expenses/{created['id']}", json=updated, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "After"
    assert body["amount"] == 200.0
    assert "updated_at" in body


def test_update_unknown_expense_returns_404(client, auth_headers):
    resp = client.put("/api/expenses/999999", json=make_expense(), headers=auth_headers)
    assert resp.status_code == 404


def test_update_expense_with_bad_category_returns_400(client, auth_headers):
    created = client.post("/api/expenses", json=make_expense(), headers=auth_headers).json()
    resp = client.put(f"/api/expenses/{created['id']}", json=make_expense(category_id=9999), headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "Category does not exist"}


# ─── Delete ─────────────────────────────────────────────────────────────────


def test_delete_expense_returns_204_with_empty_body(client, auth_headers):
    created = client.post("/api/expenses", json=make_expense(), headers=auth_headers).json()
    resp = client.delete(f"/api/expenses/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_expense_then_get_returns_404(client, auth_headers):
    created = client.post("/api/expenses", json=make_expense(), headers=auth_headers).json()
    client.delete(f"/api/expenses/{created['id']}", headers=auth_headers)
    resp = client.get(f"/api/expenses/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_unknown_expense_returns_404(client, auth_headers):
    resp = client.delete("/api/expenses/999999", headers=auth_headers)
    assert resp.status_code == 404


# ─── Ownership isolation ─────────────────────────────────────────────────────


@pytest.fixture()
def alice_expense(client, auth_headers):
    """Create one expense for alice and return its id."""
    resp = client.post("/api/expenses", json=make_expense(title="Alice private"), headers=auth_headers)
    return resp.json()["id"]


def test_isolation_bob_cannot_get_alice_expense(client, auth_headers, second_user_headers, alice_expense):
    resp = client.get(f"/api/expenses/{alice_expense}", headers=second_user_headers)
    assert resp.status_code == 404


def test_isolation_bob_cannot_update_alice_expense(client, auth_headers, second_user_headers, alice_expense):
    resp = client.put(f"/api/expenses/{alice_expense}", json=make_expense(title="Hijacked"), headers=second_user_headers)
    assert resp.status_code == 404


def test_isolation_bob_cannot_delete_alice_expense(client, auth_headers, second_user_headers, alice_expense):
    resp = client.delete(f"/api/expenses/{alice_expense}", headers=second_user_headers)
    assert resp.status_code == 404


def test_isolation_bobs_list_does_not_include_alice_expense(client, auth_headers, second_user_headers, alice_expense):
    resp = client.get("/api/expenses", headers=second_user_headers)
    ids = [e["id"] for e in resp.json()["items"]]
    assert alice_expense not in ids


def test_isolation_alice_expense_unchanged_after_bob_attempt(client, auth_headers, second_user_headers, alice_expense):
    client.put(f"/api/expenses/{alice_expense}", json=make_expense(title="Hijacked"), headers=second_user_headers)
    resp = client.get(f"/api/expenses/{alice_expense}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Alice private"


# ─── Categories ─────────────────────────────────────────────────────────────


def test_get_categories_authenticated_returns_9_items(client, auth_headers):
    resp = client.get("/api/categories", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 9


def test_get_categories_first_is_food(client, auth_headers):
    resp = client.get("/api/categories", headers=auth_headers)
    assert resp.json()[0]["name"] == "Food"


def test_get_categories_unauthenticated_returns_401(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 401


# ─── Error handling ─────────────────────────────────────────────────────────


def test_unknown_route_returns_404_json(client):
    resp = client.get("/api/nope")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body


def test_unexpected_exception_returns_500_generic(client, auth_headers):
    """Force a 500 via dependency override; confirm no traceback leaks to client."""
    from fastapi import Request

    def _boom():
        raise RuntimeError("db connection lost: password=admin internal path /data/prod.db")

    app.dependency_overrides["_boom"] = _boom

    # Override a real dependency used by a real route
    from app.dependencies import get_db
    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = _boom
    try:
        client_500 = TestClient(app, raise_server_exceptions=False)
        resp = client_500.get("/api/categories", headers=auth_headers)
        assert resp.status_code == 500
        body = resp.json()
        assert body == {"detail": "Internal server error"}
        assert "RuntimeError" not in resp.text
        assert "Traceback" not in resp.text
        assert "password" not in resp.text.lower()
        assert "/data/prod.db" not in resp.text
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


# ─── Frontend pages ─────────────────────────────────────────────────────────


def test_index_page_returns_200_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_dashboard_page_returns_200_html(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
