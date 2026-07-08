"""Application factory and ASGI entrypoint for the control-plane service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.logging_config import configure_logging, get_logger
from app.metrics import metrics_middleware, render_metrics
from app.models.common import ProblemDetail
from app.routers import deployments, environments, health
from app.services.exceptions import ServiceError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle hooks."""

    settings: Settings = app.state.settings
    logger.info(
        "service.startup",
        extra={"service": settings.service_name, "environment": settings.environment},
    )
    yield
    logger.info("service.shutdown", extra={"service": settings.service_name})


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    app = FastAPI(
        title="Enterprise DevOps Platform — Control Plane",
        description="Register environments and orchestrate deployments across the EKS estate.",
        version=settings.version,
        root_path=settings.root_path,
        lifespan=lifespan,
    )
    app.state.settings = settings

    if settings.metrics_enabled:
        app.middleware("http")(metrics_middleware)

        @app.get("/metrics", include_in_schema=False)
        def metrics() -> object:  # pragma: no cover - thin wrapper
            return render_metrics()

    app.include_router(health.router)
    app.include_router(environments.router)
    app.include_router(deployments.router)

    @app.exception_handler(ServiceError)
    async def _handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
        problem = ProblemDetail(
            title=exc.title,
            status=exc.status_code,
            detail=str(exc),
            instance=str(request.url),
        )
        return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

    return app


app = create_app()
