"""Tests for the deployments router."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_env(client: TestClient, name: str = "dev") -> None:
    client.post(
        "/api/v1/environments",
        json={"name": name, "tier": "dev", "cluster": f"edp-{name}"},
    )


def _create_deployment(client: TestClient, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "environment": "dev",
        "image_tag": "1.2.3",
        "strategy": "rolling",
        "requested_by": "ci@edp",
    }
    body.update(overrides)
    return client.post("/api/v1/deployments", json=body).json()


def test_create_deployment_requires_known_environment(client: TestClient) -> None:
    response = client.post(
        "/api/v1/deployments",
        json={
            "environment": "ghost",
            "image_tag": "1.0.0",
            "strategy": "rolling",
            "requested_by": "ci@edp",
        },
    )
    assert response.status_code == 404


def test_full_deployment_lifecycle(client: TestClient) -> None:
    _register_env(client)
    created = _create_deployment(client)
    assert created["status"] == "pending"
    deployment_id = created["id"]

    started = client.post(
        f"/api/v1/deployments/{deployment_id}/transition",
        json={"status": "in_progress"},
    )
    assert started.json()["status"] == "in_progress"

    succeeded = client.post(
        f"/api/v1/deployments/{deployment_id}/transition",
        json={"status": "succeeded", "message": "rollout complete"},
    )
    assert succeeded.json()["status"] == "succeeded"
    assert succeeded.json()["message"] == "rollout complete"


def test_transition_after_terminal_is_rejected(client: TestClient) -> None:
    _register_env(client)
    deployment_id = _create_deployment(client)["id"]
    client.post(
        f"/api/v1/deployments/{deployment_id}/transition", json={"status": "succeeded"}
    )
    again = client.post(
        f"/api/v1/deployments/{deployment_id}/transition", json={"status": "failed"}
    )
    assert again.status_code == 422


def test_rollback_only_succeeded(client: TestClient) -> None:
    _register_env(client)
    deployment_id = _create_deployment(client)["id"]
    # Still pending -> rollback should be rejected.
    assert client.post(f"/api/v1/deployments/{deployment_id}/rollback").status_code == 422

    client.post(
        f"/api/v1/deployments/{deployment_id}/transition", json={"status": "succeeded"}
    )
    rolled_back = client.post(f"/api/v1/deployments/{deployment_id}/rollback")
    assert rolled_back.status_code == 200
    assert rolled_back.json()["status"] == "rolled_back"


def test_invalid_image_tag_rejected(client: TestClient) -> None:
    _register_env(client)
    response = client.post(
        "/api/v1/deployments",
        json={
            "environment": "dev",
            "image_tag": "bad tag!!",
            "strategy": "rolling",
            "requested_by": "ci@edp",
        },
    )
    assert response.status_code == 422


def test_list_deployments_filtered_by_environment(client: TestClient) -> None:
    _register_env(client, "dev")
    _register_env(client, "prod")
    _create_deployment(client, environment="dev")
    _create_deployment(client, environment="prod")
    dev_only = client.get("/api/v1/deployments", params={"environment": "dev"}).json()
    assert len(dev_only) == 1
    assert dev_only[0]["environment"] == "dev"
