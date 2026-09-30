"""Tests for GET /api/health."""


def test_health_returns_200_with_status_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
