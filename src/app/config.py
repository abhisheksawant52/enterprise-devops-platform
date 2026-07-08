"""Application configuration loaded from the environment.

Uses ``pydantic-settings`` so configuration is typed, validated, and overridable via environment
variables. All settings are prefixed with ``EDP_`` (e.g. ``EDP_LOG_LEVEL=debug``).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the control-plane service."""

    model_config = SettingsConfigDict(
        env_prefix="EDP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service identity
    service_name: str = "edp-control-plane"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    version: str = "1.0.0"

    # HTTP server
    host: str = "0.0.0.0"  # noqa: S104 - bind-all is intentional inside the container
    port: int = Field(default=8000, ge=1, le=65535)
    root_path: str = ""

    # Logging
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    log_json: bool = True

    # Observability
    metrics_enabled: bool = True

    # Behaviour
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    max_concurrent_deployments: int = Field(default=25, ge=1)

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        return value.lower() if isinstance(value, str) else value

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""

    return Settings()
