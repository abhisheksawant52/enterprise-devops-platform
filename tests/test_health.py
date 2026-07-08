"""Tests for the health and metrics endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_returns_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "edp-control-plane"
    assert body["environment"] == "local"


def test_readyz_returns_ready(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_endpoint_exposes_prometheus(client: TestClient) -> None:
    # Generate at least one request so counters are populated.
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "edp_http_requests_total" in response.text


def test_openapi_schema_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["version"] == "1.0.0"
