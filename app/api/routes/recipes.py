"""Recipe API endpoints for CRUD operations and filtered listing."""

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_recipe_service
from app.core.responses import success_response
from app.schemas.common import StandardResponse
from app.schemas.recipe import RecipeCreate, RecipeReplace, RecipeSearchParams, RecipeUpdate
from app.services.recipe_service import RecipeService

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    recipe_data: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service),
):
    """Create a new recipe."""
    recipe = service.create_recipe(recipe_data)
    return success_response(recipe.model_dump(), "Recipe created successfully", status.HTTP_201_CREATED)


@router.get("", response_model=StandardResponse)
def list_recipes(
    title: str = Query(default=None, min_length=1, max_length=255,
                       description="Filter by title (case-insensitive substring match)"),
    is_vegetarian: bool = Query(default=None, description="Filter by vegetarian status"),
    servings: int = Query(default=None, ge=1, le=100, description="Filter by exact number of servings"),
    include_ingredients: list[str] = Query(default=[],
                                           description="Only return recipes containing all of these ingredients"),
    exclude_ingredients: list[str] = Query(default=[],
                                           description="Exclude recipes containing any of these ingredients"),
    instruction_text: str = Query(default=None, min_length=1,
                                  description="Filter by instruction text (case-insensitive substring match)"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of recipes to return"),
    offset: int = Query(default=0, ge=0, description="Number of recipes to skip for pagination"),
    service: RecipeService = Depends(get_recipe_service),
):
    """List recipes with optional filters. Returns all recipes if no filters are provided."""
    params = RecipeSearchParams(
        title=title,
        is_vegetarian=is_vegetarian,
        servings=servings,
        include_ingredients=include_ingredients,
        exclude_ingredients=exclude_ingredients,
        instruction_text=instruction_text,
    )
    paginated = service.list_recipes(params, limit=limit, offset=offset)
    return success_response(paginated.model_dump(), "Recipes fetched successfully")


@router.get("/{recipe_id}", response_model=StandardResponse)
def get_recipe(recipe_id: int, service: RecipeService = Depends(get_recipe_service)):
    """Retrieve a single recipe by ID."""
    recipe = service.get_recipe(recipe_id)
    return success_response(recipe.model_dump(), "Recipe fetched successfully")


@router.put("/{recipe_id}", response_model=StandardResponse)
def replace_recipe(
    recipe_id: int,
    recipe_data: RecipeReplace,
    service: RecipeService = Depends(get_recipe_service),
):
    """Replace a recipe entirely by ID."""
    recipe = service.replace_recipe(recipe_id, recipe_data)
    return success_response(recipe.model_dump(), "Recipe replaced successfully")


@router.patch("/{recipe_id}", response_model=StandardResponse)
def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    service: RecipeService = Depends(get_recipe_service),
):
    """Partially update a recipe by ID."""
    recipe = service.update_recipe(recipe_id, recipe_data)
    return success_response(recipe.model_dump(), "Recipe updated successfully")


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, service: RecipeService = Depends(get_recipe_service)):
    """Delete a recipe by ID."""
    service.delete_recipe(recipe_id)
