"""Unit tests for the service layer (no HTTP)."""

from __future__ import annotations

import pytest

from app.models.deployment import DeploymentCreate, DeploymentStatus, DeploymentStrategy
from app.models.environment import EnvironmentCreate, EnvironmentTier
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.registry import DeploymentService, EnvironmentService


def _env(name: str = "dev") -> EnvironmentCreate:
    return EnvironmentCreate(name=name, tier=EnvironmentTier.DEV, cluster=f"edp-{name}")


def _dep(environment: str = "dev") -> DeploymentCreate:
    return DeploymentCreate(
        environment=environment,
        image_tag="1.0.0",
        strategy=DeploymentStrategy.ROLLING,
        requested_by="tester",
    )


def test_environment_create_and_exists(environment_service: EnvironmentService) -> None:
    created = environment_service.create(_env())
    assert environment_service.exists("dev")
    assert environment_service.get("dev").id == created.id


def test_environment_duplicate_raises(environment_service: EnvironmentService) -> None:
    environment_service.create(_env())
    with pytest.raises(ConflictError):
        environment_service.create(_env())


def test_prod_environment_requires_approval() -> None:
    env = EnvironmentCreate(name="prod", tier=EnvironmentTier.PROD, cluster="edp-prod")
    service = EnvironmentService()
    created = service.create(env)
    assert created.requires_approval is True


def test_deployment_requires_environment(deployment_service: DeploymentService) -> None:
    with pytest.raises(NotFoundError):
        deployment_service.create(_dep("missing"))


def test_deployment_concurrency_limit(
    environment_service: EnvironmentService, deployment_service: DeploymentService
) -> None:
    environment_service.create(_env())
    # settings fixture caps concurrency at 3.
    for _ in range(3):
        deployment_service.create(_dep())
    with pytest.raises(ConflictError):
        deployment_service.create(_dep())


def test_deployment_transition_and_rollback(
    environment_service: EnvironmentService, deployment_service: DeploymentService
) -> None:
    environment_service.create(_env())
    deployment = deployment_service.create(_dep())
    deployment_service.transition(deployment.id, DeploymentStatus.IN_PROGRESS)
    deployment_service.transition(deployment.id, DeploymentStatus.SUCCEEDED)
    rolled = deployment_service.rollback(deployment.id)
    assert rolled.status == DeploymentStatus.ROLLED_BACK


def test_rollback_non_succeeded_raises(
    environment_service: EnvironmentService, deployment_service: DeploymentService
) -> None:
    environment_service.create(_env())
    deployment = deployment_service.create(_dep())
    with pytest.raises(ValidationError):
        deployment_service.rollback(deployment.id)


def test_status_is_terminal_property() -> None:
    assert DeploymentStatus.SUCCEEDED.is_terminal
    assert DeploymentStatus.FAILED.is_terminal
    assert not DeploymentStatus.PENDING.is_terminal
