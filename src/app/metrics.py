"""Prometheus metrics definitions and middleware.

Exposes request counters/histograms plus domain gauges (active deployments) that the observability
stack scrapes from ``/metrics``.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "edp_http_requests_total",
    "Total HTTP requests processed by the control plane.",
    labelnames=("method", "path", "status"),
)

REQUEST_LATENCY = Histogram(
    "edp_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

DEPLOYMENTS_IN_PROGRESS = Gauge(
    "edp_deployments_in_progress",
    "Number of deployments currently in a non-terminal state.",
    labelnames=("environment",),
)

DEPLOYMENTS_TOTAL = Counter(
    "edp_deployments_total",
    "Total deployments created, labelled by final/initial status.",
    labelnames=("environment", "status"),
)


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Record request count and latency for every request."""

    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    # Use the matched route template (if any) to keep label cardinality bounded.
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)

    REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    return response


def render_metrics() -> Response:
    """Return the current metrics in the Prometheus exposition format."""

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
