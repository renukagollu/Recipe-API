"""Unit tests for JsonFormatter and setup_logging."""

import json
import logging

from app.core.logging import JsonFormatter, setup_logging


def test_json_formatter_basic_log():
    """Format a simple INFO log record as valid JSON with required fields."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="hello world",
        args=None,
        exc_info=None,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "hello world"
    assert "time" in data


def test_json_formatter_includes_request_fields():
    """Include HTTP request extras (request_id, method, path, etc.) in output."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="recipe_api",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="request_completed",
        args=None,
        exc_info=None,
    )
    record.request_id = "abc-123"
    record.method = "GET"
    record.path = "/recipes"
    record.status_code = 200
    record.duration_ms = 12.5

    output = formatter.format(record)
    data = json.loads(output)

    assert data["request_id"] == "abc-123"
    assert data["method"] == "GET"
    assert data["path"] == "/recipes"
    assert data["status_code"] == 200
    assert data["duration_ms"] == 12.5


def test_json_formatter_includes_exception_info():
    """Append formatted traceback when the log record contains exc_info."""
    formatter = JsonFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="something failed",
        args=None,
        exc_info=exc_info,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert "exception" in data
    assert "ValueError" in data["exception"]
    assert "test error" in data["exception"]


def test_setup_logging_configures_root_logger():
    """Verify setup_logging sets a single JsonFormatter handler on the root logger."""
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    try:
        setup_logging()

        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0].formatter, JsonFormatter)
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
