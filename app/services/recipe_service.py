"""Service layer for recipe business logic."""

from app.core.errors import RecipeDuplicateError, RecipeNotFoundError
from app.db.models import Recipe
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recipe import (
    RecipeCreate,
    RecipeOut,
    RecipeReplace,
    RecipeSearchParams,
    RecipeUpdate,
    PaginatedRecipeResponse,
)


class RecipeService:
    """Orchestrates recipe operations between the API layer and repository."""

    def __init__(self, repository: RecipeRepository):
        """Initialize the RecipeService with a RecipeRepository instance."""
        self.repository = repository

    def create_recipe(self, recipe_data: RecipeCreate) -> RecipeOut:
        """Create a new recipe and return it as RecipeOut. Raises RecipeDuplicateError if title exists."""
        existing = self.repository.get_by_title(recipe_data.title)
        if existing is not None:
            raise RecipeDuplicateError(f"Recipe with title '{recipe_data.title}' already exists")
        recipe = self.repository.create(recipe_data)
        return self._to_output(recipe)

    def get_recipe(self, recipe_id: int) -> RecipeOut:
        """Retrieve a recipe by ID. Raises RecipeNotFoundError if not found."""
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(f"Recipe with id {recipe_id} was not found")
        return self._to_output(recipe)

    def list_recipes(self, params: RecipeSearchParams, limit: int = 10, offset: int = 0) -> PaginatedRecipeResponse:
        """Return a paginated list of recipes matching the given search filters."""
        recipes = self.repository.list_with_filters(params)
        total = len(recipes)
        paginated = recipes[offset : offset + limit]
        return PaginatedRecipeResponse(
            items=[self._to_output(recipe) for recipe in paginated],
            total=total,
            limit=limit,
            offset=offset,
        )

    def replace_recipe(self, recipe_id: int, recipe_data: RecipeReplace) -> RecipeOut:
        """Replace a recipe entirely by ID. Raises RecipeNotFoundError if not found."""
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(f"Recipe with id {recipe_id} was not found")

        replaced_recipe = self.repository.replace(recipe, recipe_data)
        return self._to_output(replaced_recipe)

    def update_recipe(self, recipe_id: int, recipe_data: RecipeUpdate) -> RecipeOut:
        """Update a recipe by ID with partial data. Raises RecipeNotFoundError if not found."""
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(f"Recipe with id {recipe_id} was not found")

        updated_recipe = self.repository.update(recipe, recipe_data)
        return self._to_output(updated_recipe)

    def delete_recipe(self, recipe_id: int) -> None:
        """Delete a recipe by ID. Raises RecipeNotFoundError if not found."""
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(f"Recipe with id {recipe_id} was not found")
        self.repository.delete(recipe)

    @staticmethod
    def _to_output(recipe: Recipe) -> RecipeOut:
        """Convert a Recipe model to a RecipeOut schema with sorted ingredient names."""
        ingredient_names = sorted(
            [item.ingredient.name for item in recipe.ingredients],
        )
        return RecipeOut(
            id=recipe.id,
            title=recipe.title,
            instructions=recipe.instructions,
            servings=recipe.servings,
            is_vegetarian=recipe.is_vegetarian,
            ingredients=ingredient_names,
        )
