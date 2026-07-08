"""Deployment orchestration endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.dependencies import get_deployment_service
from app.models.deployment import Deployment, DeploymentCreate, DeploymentStatus
from app.services.registry import DeploymentService

router = APIRouter(prefix="/api/v1/deployments", tags=["deployments"])


class TransitionRequest(BaseModel):
    """Body for advancing a deployment's status."""

    status: DeploymentStatus
    message: str | None = None


@router.post(
    "",
    response_model=Deployment,
    status_code=status.HTTP_201_CREATED,
    summary="Create a deployment",
)
def create_deployment(
    payload: DeploymentCreate,
    service: DeploymentService = Depends(get_deployment_service),
) -> Deployment:
    return service.create(payload)


@router.get("", response_model=list[Deployment], summary="List deployments")
def list_deployments(
    environment: str | None = Query(default=None, description="Filter by environment name"),
    service: DeploymentService = Depends(get_deployment_service),
) -> list[Deployment]:
    return service.list(environment=environment)


@router.get("/{deployment_id}", response_model=Deployment, summary="Get a deployment")
def get_deployment(
    deployment_id: UUID,
    service: DeploymentService = Depends(get_deployment_service),
) -> Deployment:
    return service.get(deployment_id)


@router.post(
    "/{deployment_id}/transition",
    response_model=Deployment,
    summary="Advance a deployment's status",
)
def transition_deployment(
    deployment_id: UUID,
    payload: TransitionRequest,
    service: DeploymentService = Depends(get_deployment_service),
) -> Deployment:
    return service.transition(deployment_id, payload.status, payload.message)


@router.post(
    "/{deployment_id}/rollback",
    response_model=Deployment,
    summary="Roll back a succeeded deployment",
)
def rollback_deployment(
    deployment_id: UUID,
    service: DeploymentService = Depends(get_deployment_service),
) -> Deployment:
    return service.rollback(deployment_id)
