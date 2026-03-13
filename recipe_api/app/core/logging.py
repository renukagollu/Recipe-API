"""Structured JSON logging configuration and request logging middleware."""

import json
import logging
import sys
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON with optional HTTP request fields."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }

        for field_name in [
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
        ]:
            field_value = getattr(record, field_name, None)
            if field_value is not None:
                log_data[field_name] = field_value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure the root logger with JSON formatting and the app's log level."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)


logger = logging.getLogger("recipe_api")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Logs each HTTP request with a unique request ID, method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        """Process the request, log completion details, and add X-Request-ID header."""
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
