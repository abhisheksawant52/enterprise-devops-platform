"""Dependency-injection wiring for FastAPI routers.

Service singletons are created once at import time and shared across requests. They are exposed via
FastAPI ``Depends`` so tests can override them with ``app.dependency_overrides``.
"""

from __future__ import annotations

from app.config import Settings, get_settings
from app.services.registry import DeploymentService, EnvironmentService

_settings: Settings = get_settings()
_environment_service = EnvironmentService()
_deployment_service = DeploymentService(_environment_service, _settings)


def get_environment_service() -> EnvironmentService:
    """Return the shared :class:`EnvironmentService`."""

    return _environment_service


def get_deployment_service() -> DeploymentService:
    """Return the shared :class:`DeploymentService`."""

    return _deployment_service
