"""Tests for the environments router."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "name": "dev",
        "tier": "dev",
        "cluster": "edp-dev",
        "namespace": "edp-system",
        "region": "ap-south-1",
    }
    body.update(overrides)
    return body


def test_create_and_get_environment(client: TestClient) -> None:
    create = client.post("/api/v1/environments", json=_payload())
    assert create.status_code == 201
    created = create.json()
    assert created["name"] == "dev"
    assert created["tier"] == "dev"

    fetched = client.get("/api/v1/environments/dev")
    assert fetched.status_code == 200
    assert fetched.json()["cluster"] == "edp-dev"


def test_create_duplicate_environment_conflicts(client: TestClient) -> None:
    assert client.post("/api/v1/environments", json=_payload()).status_code == 201
    duplicate = client.post("/api/v1/environments", json=_payload())
    assert duplicate.status_code == 409
    assert duplicate.json()["title"] == "Conflict"


def test_get_unknown_environment_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/environments/nope")
    assert response.status_code == 404


def test_invalid_environment_name_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/environments", json=_payload(name="Bad Name!"))
    assert response.status_code == 422


def test_list_environments_is_sorted(client: TestClient) -> None:
    client.post("/api/v1/environments", json=_payload(name="prod", tier="prod", cluster="edp-prod"))
    client.post("/api/v1/environments", json=_payload(name="dev", cluster="edp-dev"))
    names = [e["name"] for e in client.get("/api/v1/environments").json()]
    assert names == ["dev", "prod"]
