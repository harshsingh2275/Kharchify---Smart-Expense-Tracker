"""Tests for GET /api/summary (monthly spending summary)."""

import datetime
from datetime import timezone

from tests.conftest import make_expense


# ─── Empty month ────────────────────────────────────────────────────────────


def test_summary_empty_month_returns_zeros_and_empty_list(client, auth_headers):
    resp = client.get("/api/summary?month=2020-01", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["month"] == "2020-01"
    assert body["total_spent"] == 0
    assert body["expense_count"] == 0
    assert body["by_category"] == []


# ─── Response shape ──────────────────────────────────────────────────────────


def test_summary_has_all_required_fields(client, auth_headers):
    resp = client.get("/api/summary?month=2020-01", headers=auth_headers)
    body = resp.json()
    for key in ("month", "total_spent", "expense_count", "by_category"):
        assert key in body


# ─── Two categories, two months ─────────────────────────────────────────────


def _create_two_month_expenses(client, headers):
    """Create known expenses in Jan and Feb 2026 for two categories."""
    # January: Food 100.00 + Transport 200.00
    client.post("/api/expenses", json=make_expense(amount=100.00, category_id=1, expense_date="2026-01-10"), headers=headers)
    client.post("/api/expenses", json=make_expense(amount=200.00, category_id=2, expense_date="2026-01-20"), headers=headers)
    # February: Food 50.00
    client.post("/api/expenses", json=make_expense(amount=50.00, category_id=1, expense_date="2026-02-05"), headers=headers)


def test_summary_correct_totals_for_specified_month(client, auth_headers):
    _create_two_month_expenses(client, auth_headers)
    resp = client.get("/api/summary?month=2026-01", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_spent"] == 300.0
    assert body["expense_count"] == 2


def test_summary_per_category_totals_and_counts(client, auth_headers):
    _create_two_month_expenses(client, auth_headers)
    resp = client.get("/api/summary?month=2026-01", headers=auth_headers)
    categories = {row["category_name"]: row for row in resp.json()["by_category"]}
    assert categories["Transport"]["total"] == 200.0
    assert categories["Transport"]["count"] == 1
    assert categories["Food"]["total"] == 100.0
    assert categories["Food"]["count"] == 1


def test_summary_by_category_sorted_by_total_descending(client, auth_headers):
    _create_two_month_expenses(client, auth_headers)
    resp = client.get("/api/summary?month=2026-01", headers=auth_headers)
    totals = [row["total"] for row in resp.json()["by_category"]]
    assert totals == sorted(totals, reverse=True)


def test_summary_only_categories_with_expenses_appear(client, auth_headers):
    """Categories with zero spending must not appear."""
    _create_two_month_expenses(client, auth_headers)
    resp = client.get("/api/summary?month=2026-01", headers=auth_headers)
    # Only Food and Transport should appear; the other 7 categories have no expenses
    assert len(resp.json()["by_category"]) == 2


def test_summary_excludes_other_months(client, auth_headers):
    """February expenses must not appear in January summary."""
    _create_two_month_expenses(client, auth_headers)
    resp = client.get("/api/summary?month=2026-02", headers=auth_headers)
    body = resp.json()
    # Only the Feb Food expense should appear
    assert body["total_spent"] == 50.0
    assert body["expense_count"] == 1
    assert len(body["by_category"]) == 1
    assert body["by_category"][0]["category_name"] == "Food"


# ─── Default month ───────────────────────────────────────────────────────────


def test_summary_default_month_is_current_utc_month(client, auth_headers):
    current_month = datetime.datetime.now(timezone.utc).strftime("%Y-%m")
    resp = client.get("/api/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["month"] == current_month


# ─── Rounding ────────────────────────────────────────────────────────────────


def test_summary_totals_have_at_most_2_decimal_places(client, auth_headers):
    client.post("/api/expenses", json=make_expense(amount=10.999, expense_date="2026-03-01"), headers=auth_headers)
    resp = client.get("/api/summary?month=2026-03", headers=auth_headers)
    total = resp.json()["total_spent"]
    # 10.999 rounds to 11.0 at creation; summary sum should be clean
    assert round(total, 2) == total


# ─── User isolation ──────────────────────────────────────────────────────────


def test_summary_only_includes_current_user_expenses(client, auth_headers, second_user_headers):
    # Alice spends
    client.post("/api/expenses", json=make_expense(amount=999.00, expense_date="2026-04-01"), headers=auth_headers)
    # Bob's summary for the same month must be zero
    resp = client.get("/api/summary?month=2026-04", headers=second_user_headers)
    assert resp.json()["total_spent"] == 0
    assert resp.json()["expense_count"] == 0
