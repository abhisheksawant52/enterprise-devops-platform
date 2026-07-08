"""Shared pytest fixtures.

Each test gets a freshly-wired application with isolated service instances so state does not leak
between tests.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_deployment_service, get_environment_service
from app.main import create_app
from app.services.registry import DeploymentService, EnvironmentService


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="local", log_json=False, max_concurrent_deployments=3)


@pytest.fixture
def environment_service() -> EnvironmentService:
    return EnvironmentService()


@pytest.fixture
def deployment_service(
    environment_service: EnvironmentService, settings: Settings
) -> DeploymentService:
    return DeploymentService(environment_service, settings)


@pytest.fixture
def app(
    settings: Settings,
    environment_service: EnvironmentService,
    deployment_service: DeploymentService,
) -> FastAPI:
    application = create_app(settings)
    application.dependency_overrides[get_environment_service] = lambda: environment_service
    application.dependency_overrides[get_deployment_service] = lambda: deployment_service
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
