"""Structured logging configuration.

Emits JSON log lines in non-local environments so that logs are directly ingestible by Loki /
CloudWatch, and human-readable lines locally.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON documents."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Attach any structured extras attached via ``logger.info(..., extra={...})``.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


_RESERVED_ATTRS = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime"}


def configure_logging(*, level: str = "info", json_output: bool = True) -> None:
    """Configure the root logger for the service."""

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Quiet noisy access logs; we emit our own request middleware logs.
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""

    return logging.getLogger(name)
