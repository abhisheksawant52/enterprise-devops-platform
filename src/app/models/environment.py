"""Environment domain models.

An *environment* represents a deployment target (an EKS cluster / namespace pair) that the control
plane can promote workloads into.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EnvironmentTier(str, Enum):
    """Environment criticality tier."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class EnvironmentCreate(BaseModel):
    """Payload to register a new environment."""

    name: str = Field(min_length=2, max_length=40)
    tier: EnvironmentTier
    cluster: str = Field(min_length=2, max_length=63)
    namespace: str = Field(default="edp-system", min_length=1, max_length=63)
    region: str = Field(default="ap-south-1")

    @field_validator("name", "cluster", "namespace")
    @classmethod
    def _dns_safe(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not all(ch.isalnum() or ch == "-" for ch in normalized):
            raise ValueError("must contain only lowercase alphanumerics and hyphens")
        return normalized


class Environment(EnvironmentCreate):
    """A persisted environment."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def requires_approval(self) -> bool:
        """Production promotions require a manual approval gate."""

        return self.tier == EnvironmentTier.PROD
