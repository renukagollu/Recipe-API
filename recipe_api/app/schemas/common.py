"""Common Pydantic models for API responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    """Standard error response body."""

    code: str
    details: str

    model_config = ConfigDict(json_schema_extra={"example": {"code": "NOT_FOUND", "details": "Recipe not found."}})


class StandardResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    message: str
    data: Any | None = None
    error: ErrorBody | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Recipe fetched successfully",
                "data": {
                    "id": 1,
                    "title": "Chicken Biryani",
                    "instructions": "Marinate chicken, soak basmati rice and cook it for 45mins.",
                    "servings": 5,
                    "is_vegetarian": False,
                    "ingredients": [
                        "Chicken",
                        "Basmati rice",
                        "ghee",
                        "salt",
                        "whole spices",
                    ],
                },
                "error": None,
            }
        }
    )
