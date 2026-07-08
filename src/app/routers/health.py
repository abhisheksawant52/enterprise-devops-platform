"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.common import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthStatus, summary="Liveness probe")
def healthz(settings: Settings = Depends(get_settings)) -> HealthStatus:
    """Return a static liveness signal.

    Kubernetes uses this to decide whether to restart the pod. It must not depend on downstream
    systems, so it always reports ``ok`` if the process is serving requests.
    """

    return HealthStatus(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
    )


@router.get("/readyz", response_model=HealthStatus, summary="Readiness probe")
def readyz(settings: Settings = Depends(get_settings)) -> HealthStatus:
    """Return readiness.

    In a full implementation this would check the database connection pool and any hard dependencies.
    Here the in-memory store is always ready once the process is up.
    """

    return HealthStatus(
        status="ready",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
    )
