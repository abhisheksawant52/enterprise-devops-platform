"""Deployment domain models.

A *deployment* is a single attempt to roll a given image tag into an environment. It moves through a
state machine: ``pending -> in_progress -> {succeeded, failed}`` and may be ``rolled_back``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

_IMAGE_TAG_RE = re.compile(r"^[\w][\w.-]{0,127}$")


class DeploymentStatus(str, Enum):
    """Lifecycle states for a deployment."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

    @property
    def is_terminal(self) -> bool:
        return self in {
            DeploymentStatus.SUCCEEDED,
            DeploymentStatus.FAILED,
            DeploymentStatus.ROLLED_BACK,
        }


class DeploymentStrategy(str, Enum):
    """Supported rollout strategies."""

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


class DeploymentCreate(BaseModel):
    """Payload to create a deployment."""

    environment: str = Field(min_length=2, max_length=40)
    image_tag: str = Field(min_length=1, max_length=128)
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    requested_by: str = Field(min_length=1, max_length=120)

    @field_validator("image_tag")
    @classmethod
    def _valid_tag(cls, value: str) -> str:
        if not _IMAGE_TAG_RE.match(value):
            raise ValueError("invalid OCI image tag")
        return value


class Deployment(BaseModel):
    """A persisted deployment record."""

    id: UUID = Field(default_factory=uuid4)
    environment: str
    image_tag: str
    strategy: DeploymentStrategy
    requested_by: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str | None = None

    def transition_to(self, status: DeploymentStatus, message: str | None = None) -> None:
        """Advance the deployment to a new state, updating the timestamp."""

        self.status = status
        self.message = message
        self.updated_at = datetime.now(timezone.utc)
