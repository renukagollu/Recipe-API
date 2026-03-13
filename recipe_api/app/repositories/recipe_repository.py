"""Repository layer for Recipe database operations."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Ingredient, Recipe, RecipeIngredient
from app.schemas.recipe import RecipeCreate, RecipeReplace, RecipeSearchParams, RecipeUpdate


class RecipeRepository:
    """Handles all database operations for Recipe entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, recipe_data: RecipeCreate) -> Recipe:
        """Create a new recipe and return it with ingredients loaded."""
        recipe = Recipe(
            title=recipe_data.title,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            is_vegetarian=recipe_data.is_vegetarian,
        )
        self.db.add(recipe)
        self.db.flush()

        self._replace_ingredients(recipe, recipe_data.ingredients)
        self.db.commit()
        self.db.refresh(recipe)
        return self._get_with_ingredients(recipe.id)

    def get_by_id(self, recipe_id: int) -> Recipe | None:
        """Retrieve a recipe by ID with ingredients loaded, or None if not found."""
        return self._get_with_ingredients(recipe_id)

    def get_by_title(self, title: str) -> Recipe | None:
        """Retrieve a recipe by exact title (case-insensitive), or None if not found."""
        query = select(Recipe).where(func.lower(Recipe.title) == title.lower())
        return self.db.scalar(query)

    def list_with_filters(self, params: RecipeSearchParams) -> list[Recipe]:
        """Return recipes matching the given search filters, ordered by ID ascending."""
        query: Select[tuple[Recipe]] = (
            select(Recipe)
            .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
            .distinct()
        )

        if params.title:
            query = query.where(Recipe.title.ilike(f"%{params.title}%"))

        if params.is_vegetarian is not None:
            query = query.where(Recipe.is_vegetarian == params.is_vegetarian)

        if params.servings is not None:
            query = query.where(Recipe.servings == params.servings)

        if params.instruction_text:
            query = query.where(Recipe.instructions.ilike(f"%{params.instruction_text}%"))

        if params.include_ingredients:
            include_subquery = (
                select(RecipeIngredient.recipe_id)
                .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
                .where(Ingredient.name.in_(params.include_ingredients))
                .group_by(RecipeIngredient.recipe_id)
                .having(func.count(func.distinct(Ingredient.name)) == len(params.include_ingredients))
            )
            query = query.where(Recipe.id.in_(include_subquery))

        if params.exclude_ingredients:
            exclude_subquery = (
                select(RecipeIngredient.recipe_id)
                .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
                .where(Ingredient.name.in_(params.exclude_ingredients))
            )
            query = query.where(~Recipe.id.in_(exclude_subquery))

        query = query.order_by(Recipe.id.asc())
        return list(self.db.scalars(query).all())

    def update(self, recipe: Recipe, recipe_data: RecipeUpdate) -> Recipe:
        """Apply partial updates to a recipe and return the refreshed instance."""
        update_data = recipe_data.model_dump(exclude_unset=True)

        if "title" in update_data:
            recipe.title = update_data["title"]
        if "instructions" in update_data:
            recipe.instructions = update_data["instructions"]
        if "servings" in update_data:
            recipe.servings = update_data["servings"]
        if "is_vegetarian" in update_data:
            recipe.is_vegetarian = update_data["is_vegetarian"]
        if "ingredients" in update_data:
            self._replace_ingredients(recipe, update_data["ingredients"])

        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return self._get_with_ingredients(recipe.id)

    def replace(self, recipe: Recipe, recipe_data: RecipeReplace) -> Recipe:
        """Replace all fields on a recipe unconditionally and return the refreshed instance."""
        recipe.title = recipe_data.title
        recipe.instructions = recipe_data.instructions
        recipe.servings = recipe_data.servings
        recipe.is_vegetarian = recipe_data.is_vegetarian
        self._replace_ingredients(recipe, recipe_data.ingredients)

        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return self._get_with_ingredients(recipe.id)

    def delete(self, recipe: Recipe) -> None:
        """Delete a recipe from the database."""
        self.db.delete(recipe)
        self.db.commit()

    def _replace_ingredients(self, recipe: Recipe, ingredient_names: list[str]) -> None:
        """Remove existing ingredient links and create new ones from the given names."""
        existing_links = list(recipe.ingredients)
        for link in existing_links:
            self.db.delete(link)
        self.db.flush()
        self.db.expire(recipe, ["ingredients"])

        for ingredient_name in ingredient_names:
            ingredient = self.db.scalar(select(Ingredient).where(Ingredient.name == ingredient_name))
            if ingredient is None:
                ingredient = Ingredient(name=ingredient_name)
                self.db.add(ingredient)
                self.db.flush()

            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
            )
            self.db.add(recipe_ingredient)

        self.db.flush()

    def _get_with_ingredients(self, recipe_id: int) -> Recipe | None:
        """Retrieve a recipe by ID with ingredients eagerly loaded."""
        query = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        )
        return self.db.scalar(query)
