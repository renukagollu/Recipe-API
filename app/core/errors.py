"""Custom exceptions for the application."""


class RecipeNotFoundError(Exception):
    """Exception raised when a recipe is not found."""

    pass


class RecipeDuplicateError(Exception):
    """Exception raised when a recipe with the same title already exists."""

    pass
