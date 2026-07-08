"""Shared response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health/readiness response body."""

    status: str = Field(examples=["ok"])
    service: str
    version: str
    environment: str


class ProblemDetail(BaseModel):
    """RFC 7807-style error payload."""

    title: str
    status: int
    detail: str
    instance: str | None = None
