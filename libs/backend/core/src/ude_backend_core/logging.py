from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="unbound",
)


class RequestContextFilter(logging.Filter):
    """Attach the current correlation identifier to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """Emit compact JSON without serializing request payloads or credentials."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "unbound"),
        }
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging(level: str) -> None:
    """Configure process logging once with a structured stdout handler."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(RequestContextFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())
