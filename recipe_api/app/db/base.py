"""This module imports all the database models so that they can be easily accessed from other parts of the
application."""

from app.db.models import Ingredient, Recipe, RecipeIngredient

__all__ = ["Recipe", "Ingredient", "RecipeIngredient"]
