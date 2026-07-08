"""In-memory service layer for environments and deployments.

The registry deliberately abstracts persistence behind a thread-safe in-memory store. In a production
deployment this would be backed by PostgreSQL (RDS); the service API is written so that swapping the
backing store does not change the router or model code.
"""

from __future__ import annotations

import threading
from uuid import UUID

from app.config import Settings
from app.logging_config import get_logger
from app.metrics import DEPLOYMENTS_IN_PROGRESS, DEPLOYMENTS_TOTAL
from app.models.deployment import (
    Deployment,
    DeploymentCreate,
    DeploymentStatus,
)
from app.models.environment import Environment, EnvironmentCreate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError

logger = get_logger(__name__)


class EnvironmentService:
    """Manage the lifecycle of deployment environments."""

    def __init__(self) -> None:
        self._environments: dict[str, Environment] = {}
        self._lock = threading.RLock()

    def create(self, payload: EnvironmentCreate) -> Environment:
        with self._lock:
            if payload.name in self._environments:
                raise ConflictError(f"environment '{payload.name}' already exists")
            environment = Environment(**payload.model_dump())
            self._environments[environment.name] = environment
            logger.info(
                "environment.created",
                extra={"environment": environment.name, "tier": environment.tier.value},
            )
            return environment

    def get(self, name: str) -> Environment:
        with self._lock:
            environment = self._environments.get(name)
            if environment is None:
                raise NotFoundError(f"environment '{name}' not found")
            return environment

    def list(self) -> list[Environment]:
        with self._lock:
            return sorted(self._environments.values(), key=lambda e: e.name)

    def exists(self, name: str) -> bool:
        with self._lock:
            return name in self._environments


class DeploymentService:
    """Create and drive deployments through their lifecycle."""

    def __init__(self, environments: EnvironmentService, settings: Settings) -> None:
        self._environments = environments
        self._settings = settings
        self._deployments: dict[UUID, Deployment] = {}
        self._lock = threading.RLock()

    def create(self, payload: DeploymentCreate) -> Deployment:
        # An environment must be registered before it can be deployed to.
        if not self._environments.exists(payload.environment):
            raise NotFoundError(f"environment '{payload.environment}' not found")

        with self._lock:
            in_progress = sum(
                1
                for d in self._deployments.values()
                if d.environment == payload.environment and not d.status.is_terminal
            )
            if in_progress >= self._settings.max_concurrent_deployments:
                raise ConflictError(
                    "max concurrent deployments reached for "
                    f"environment '{payload.environment}'"
                )

            deployment = Deployment(**payload.model_dump())
            self._deployments[deployment.id] = deployment

        DEPLOYMENTS_TOTAL.labels(payload.environment, deployment.status.value).inc()
        DEPLOYMENTS_IN_PROGRESS.labels(payload.environment).inc()
        logger.info(
            "deployment.created",
            extra={
                "deployment_id": str(deployment.id),
                "environment": deployment.environment,
                "image_tag": deployment.image_tag,
                "strategy": deployment.strategy.value,
            },
        )
        return deployment

    def get(self, deployment_id: UUID) -> Deployment:
        with self._lock:
            deployment = self._deployments.get(deployment_id)
            if deployment is None:
                raise NotFoundError(f"deployment '{deployment_id}' not found")
            return deployment

    def list(self, environment: str | None = None) -> list[Deployment]:
        with self._lock:
            values = list(self._deployments.values())
        if environment is not None:
            values = [d for d in values if d.environment == environment]
        return sorted(values, key=lambda d: d.created_at, reverse=True)

    def transition(
        self, deployment_id: UUID, status: DeploymentStatus, message: str | None = None
    ) -> Deployment:
        with self._lock:
            deployment = self.get(deployment_id)
            if deployment.status.is_terminal:
                raise ValidationError(
                    f"deployment '{deployment_id}' is already terminal "
                    f"({deployment.status.value})"
                )
            was_active = not deployment.status.is_terminal
            deployment.transition_to(status, message)

        if was_active and status.is_terminal:
            DEPLOYMENTS_IN_PROGRESS.labels(deployment.environment).dec()
        DEPLOYMENTS_TOTAL.labels(deployment.environment, status.value).inc()
        logger.info(
            "deployment.transition",
            extra={"deployment_id": str(deployment_id), "status": status.value},
        )
        return deployment

    def rollback(self, deployment_id: UUID) -> Deployment:
        deployment = self.get(deployment_id)
        if deployment.status != DeploymentStatus.SUCCEEDED:
            raise ValidationError("only succeeded deployments can be rolled back")
        with self._lock:
            deployment.transition_to(
                DeploymentStatus.ROLLED_BACK, message="manual rollback requested"
            )
        DEPLOYMENTS_TOTAL.labels(deployment.environment, DeploymentStatus.ROLLED_BACK.value).inc()
        logger.warning(
            "deployment.rolled_back",
            extra={"deployment_id": str(deployment_id)},
        )
        return deployment
