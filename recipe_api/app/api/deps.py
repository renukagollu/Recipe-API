"""FastAPI dependency providers for service instances."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.recipe_repository import RecipeRepository
from app.services.recipe_service import RecipeService


def get_recipe_service(db: Session = Depends(get_db)) -> RecipeService:
    """Provide a RecipeService instance wired with a database session."""
    repository = RecipeRepository(db)
    return RecipeService(repository)
