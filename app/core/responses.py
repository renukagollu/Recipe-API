"""Standardized API response helpers for success and error cases."""

from typing import Any

from fastapi.responses import JSONResponse


def success_response(data: Any, message: str, status_code: int = 200) -> JSONResponse:
    """Return a standardized success JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "error": None,
        },
    )


def error_response(message: str, error_code: str, status_code: int) -> JSONResponse:
    """Return a standardized error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": error_code,
                "details": message,
            },
        },
    )
