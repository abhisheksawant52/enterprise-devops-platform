"""Environment management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.dependencies import get_environment_service
from app.models.environment import Environment, EnvironmentCreate
from app.services.registry import EnvironmentService

router = APIRouter(prefix="/api/v1/environments", tags=["environments"])


@router.post(
    "",
    response_model=Environment,
    status_code=status.HTTP_201_CREATED,
    summary="Register an environment",
)
def create_environment(
    payload: EnvironmentCreate,
    service: EnvironmentService = Depends(get_environment_service),
) -> Environment:
    return service.create(payload)


@router.get("", response_model=list[Environment], summary="List environments")
def list_environments(
    service: EnvironmentService = Depends(get_environment_service),
) -> list[Environment]:
    return service.list()


@router.get("/{name}", response_model=Environment, summary="Get an environment")
def get_environment(
    name: str,
    service: EnvironmentService = Depends(get_environment_service),
) -> Environment:
    return service.get(name)
