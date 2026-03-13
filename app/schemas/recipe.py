"""Pydantic schemas for recipe creation, update, output, search, and pagination."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RecipeCreate(BaseModel):
    """Schema for creating a new recipe. All fields are required."""

    title: str = Field(..., min_length=1, max_length=255)
    instructions: str = Field(..., min_length=1)
    servings: int = Field(..., ge=1, le=100)
    is_vegetarian: bool = Field(...)
    ingredients: list[str] = Field(default_factory=list, min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
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
            }
        }
    }

    @field_validator("ingredients")
    @classmethod
    def clean_ingredients(cls, value: list[str]) -> list[str]:
        """Strip whitespace, lowercase, and deduplicate ingredients."""
        clean_list = []
        seen = set()

        for item in value:
            clean_item = item.strip().lower()
            if not clean_item:
                continue
            if clean_item not in seen:
                clean_list.append(clean_item)
                seen.add(clean_item)

        if not clean_list:
            raise ValueError("At least one ingredient is required")

        return clean_list


class RecipeUpdate(BaseModel):
    """Schema for partial recipe updates. All fields are optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    instructions: Optional[str] = Field(default=None, min_length=1)
    servings: Optional[int] = Field(default=None, ge=1, le=100)
    is_vegetarian: Optional[bool] = None
    ingredients: Optional[list[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Chicken Biryani Special",
                "instructions": "Add saffron and fried onions for extra flavor.",
                "servings": 6,
                "is_vegetarian": False,
                "ingredients": [
                    "Chicken",
                    "Basmati rice",
                    "ghee",
                    "salt",
                    "whole spices",
                    "saffron",
                    "fried onions",
                ],
            }
        }
    }

    @field_validator("ingredients")
    @classmethod
    def clean_ingredients(cls, value: list[str]) -> list[str]:
        """Strip whitespace, lowercase, and deduplicate ingredients."""
        clean_list = []
        seen = set()

        for item in value:
            clean_item = item.strip().lower()
            if not clean_item:
                continue
            if clean_item not in seen:
                clean_list.append(clean_item)
                seen.add(clean_item)

        if not clean_list:
            raise ValueError("At least one ingredient is required")

        return clean_list

class RecipeReplace(BaseModel):
    """Schema for full recipe replacement via PUT. All fields are required."""

    title: str = Field(..., min_length=1, max_length=255)
    instructions: str = Field(..., min_length=1)
    servings: int = Field(..., ge=1, le=100)
    is_vegetarian: bool = Field(...)
    ingredients: list[str] = Field(default_factory=list, min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Chicken Biryani Special",
                "instructions": "Add saffron and fried onions for extra flavor.",
                "servings": 6,
                "is_vegetarian": False,
                "ingredients": [
                    "Chicken",
                    "Basmati rice",
                    "ghee",
                    "salt",
                    "whole spices",
                    "saffron",
                    "fried onions",
                ],
            }
        }
    }

    @field_validator("ingredients")
    @classmethod
    def clean_ingredients(cls, value: list[str]) -> list[str]:
        """Strip whitespace, lowercase, and deduplicate ingredients."""
        clean_list = []
        seen = set()

        for item in value:
            clean_item = item.strip().lower()
            if not clean_item:
                continue
            if clean_item not in seen:
                clean_list.append(clean_item)
                seen.add(clean_item)

        if not clean_list:
            raise ValueError("At least one ingredient is required")

        return clean_list


class RecipeOut(BaseModel):
    """Schema for recipe API output."""

    id: int
    title: str
    instructions: str
    servings: int
    is_vegetarian: bool
    ingredients: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
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
            }
        }
    }


class RecipeSearchParams(BaseModel):
    """Optional search filters for listing recipes."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter recipes by title "
                                                                       "(case-insensitive substring match)")
    is_vegetarian: Optional[bool] = Field(None, description="Filter recipes by vegetarian status")
    servings: Optional[int] = Field(default=None, ge=1, le=100, description="Filter recipes by number of servings")
    include_ingredients: Optional[list[str]] = Field(default_factory=list,
                                           description="Filter recipes that include all of these ingredients")
    exclude_ingredients: Optional[list[str]] = Field(default_factory=list,
                                           description="Filter recipes that exclude any of these ingredients")
    instruction_text: Optional[str] = Field(None, min_length=1, description="Filter recipes by instruction text ")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "biryani",
                "is_vegetarian": False,
                "servings": 5,
                "include_ingredients": ["chicken"],
                "exclude_ingredients": ["peas"],
                "instruction_text": "marinate",
            }
        }
    }

    @field_validator("include_ingredients", "exclude_ingredients")
    @classmethod
    def clean_filter_list(cls, value: list[str]) -> list[str]:
        """Strip whitespace, lowercase, and deduplicate filter ingredient lists."""
        clean_list = []
        seen = set()

        for item in value:
            clean_item = item.strip().lower()
            if clean_item and clean_item not in seen:
                clean_list.append(clean_item)
                seen.add(clean_item)

        return clean_list


class PaginatedRecipeResponse(BaseModel):
    """Paginated list of recipes with metadata."""

    items: list[RecipeOut]
    total: int
    limit: int
    offset: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
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
                    }
                ],
                "total": 25,
                "limit": 10,
                "offset": 0,
            }
        }
    }
