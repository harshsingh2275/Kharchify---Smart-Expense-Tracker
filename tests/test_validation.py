"""Tests for input validation (422 format) and boundary rules."""

import datetime

import pytest

from tests.conftest import make_expense


# ─── Helper ────────────────────────────────────────────────────────────────


def assert_422(resp, *, expected_fields: list[str] | None = None) -> None:
    """Assert a 422 response with the correct API.md structure."""
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["detail"] == "Validation failed", f"Wrong detail: {body.get('detail')}"
    assert isinstance(body["errors"], list) and len(body["errors"]) > 0
    for err in body["errors"]:
        assert "field" in err, f"Missing 'field' key in error: {err}"
        assert "message" in err, f"Missing 'message' key in error: {err}"
    if expected_fields:
        returned_fields = {e["field"] for e in body["errors"]}
        for f in expected_fields:
            assert f in returned_fields, f"Expected field '{f}' in errors, got: {returned_fields}"


# ─── Register validation ────────────────────────────────────────────────────


@pytest.mark.parametrize("username", ["ab", "x" * 31, "al ice", "al@ce", ""])
def test_register_invalid_username_returns_422(client, username):
    resp = client.post("/api/auth/register", json={"username": username, "password": "Secret123"})
    assert_422(resp, expected_fields=["username"])


@pytest.mark.parametrize("password", ["short1", "x" * 73])
def test_register_invalid_password_returns_422(client, password):
    resp = client.post("/api/auth/register", json={"username": "validuser", "password": password})
    assert_422(resp, expected_fields=["password"])


# ─── Expense create validation ──────────────────────────────────────────────


def test_expense_missing_title_returns_422(client, auth_headers):
    payload = make_expense()
    del payload["title"]
    resp = client.post("/api/expenses", json=payload, headers=auth_headers)
    assert_422(resp, expected_fields=["title"])


def test_expense_blank_title_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(title="   "), headers=auth_headers)
    assert_422(resp, expected_fields=["title"])


def test_expense_title_101_chars_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(title="a" * 101), headers=auth_headers)
    assert_422(resp, expected_fields=["title"])


@pytest.mark.parametrize("amount", [0, -1, -100, "abc"])
def test_expense_invalid_amount_returns_422(client, auth_headers, amount):
    resp = client.post("/api/expenses", json=make_expense(amount=amount), headers=auth_headers)
    assert_422(resp, expected_fields=["amount"])


def test_expense_amount_over_limit_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(amount=10_000_001), headers=auth_headers)
    assert_422(resp, expected_fields=["amount"])


def test_expense_amount_rounded_to_2_decimals(client, auth_headers):
    """10.999 must be stored and returned as 11.0."""
    resp = client.post("/api/expenses", json=make_expense(amount=10.999), headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["amount"] == 11.0


def test_expense_category_id_zero_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(category_id=0), headers=auth_headers)
    assert_422(resp, expected_fields=["category_id"])


def test_expense_category_id_999_returns_400_not_422(client, auth_headers):
    """Unknown category_id passes Pydantic validation but fails the business check -> 400."""
    resp = client.post("/api/expenses", json=make_expense(category_id=999), headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "Category does not exist"}


def test_expense_bad_date_format_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(expense_date="01-15-2026"), headers=auth_headers)
    assert_422(resp, expected_fields=["expense_date"])


def test_expense_future_date_returns_422(client, auth_headers):
    future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    resp = client.post("/api/expenses", json=make_expense(expense_date=future), headers=auth_headers)
    assert_422(resp, expected_fields=["expense_date"])


def test_expense_note_301_chars_returns_422(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(note="x" * 301), headers=auth_headers)
    assert_422(resp, expected_fields=["note"])


def test_expense_note_empty_string_stored_as_null(client, auth_headers):
    resp = client.post("/api/expenses", json=make_expense(note=""), headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["note"] is None


# ─── List / pagination validation ───────────────────────────────────────────


@pytest.mark.parametrize("limit", [0, 101])
def test_list_invalid_limit_returns_422(client, auth_headers, limit):
    resp = client.get(f"/api/expenses?limit={limit}", headers=auth_headers)
    assert_422(resp, expected_fields=["limit"])


def test_list_negative_offset_returns_422(client, auth_headers):
    resp = client.get("/api/expenses?offset=-1", headers=auth_headers)
    assert_422(resp, expected_fields=["offset"])


# ─── Summary validation ──────────────────────────────────────────────────────


@pytest.mark.parametrize("month", ["abc", "2026-13", "2026-00", "26-10", "2026/10"])
def test_summary_invalid_month_returns_422(client, auth_headers, month):
    resp = client.get(f"/api/summary?month={month}", headers=auth_headers)
    assert_422(resp, expected_fields=["month"])


# ─── 422 error format structure ─────────────────────────────────────────────


def test_422_body_structure_has_detail_and_errors_list(client):
    """Confirm the 422 envelope exactly matches API.md."""
    resp = client.post("/api/auth/register", json={"username": "x", "password": "short"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"] == "Validation failed"
    assert isinstance(body["errors"], list)
    for err in body["errors"]:
        assert set(err.keys()) >= {"field", "message"}
