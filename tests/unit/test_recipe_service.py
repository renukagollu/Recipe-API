"""Unit tests for RecipeService using a FakeRepository."""

from types import SimpleNamespace

import pytest

from app.core.errors import RecipeDuplicateError, RecipeNotFoundError
from app.schemas.recipe import RecipeCreate, RecipeReplace, RecipeSearchParams, RecipeUpdate
from app.services.recipe_service import RecipeService


class FakeRepository:
    """In-memory repository stub for isolating service-layer tests."""

    def __init__(self):
        self.items = {}
        self.next_id = 1

    def create(self, recipe_data):
        """Create a new recipe with a unique ID and store it in memory."""
        recipe = self._make_recipe(
            recipe_id=self.next_id,
            title=recipe_data.title,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            is_vegetarian=recipe_data.is_vegetarian,
            ingredients=recipe_data.ingredients,
        )
        self.items[self.next_id] = recipe
        self.next_id += 1
        return recipe

    def get_by_id(self, recipe_id):
        """Return the recipe with the given ID, or None if it doesn't exist."""
        return self.items.get(recipe_id)

    def get_by_title(self, title):
        """Return the recipe with the given title (case-insensitive), or None if it doesn't exist."""
        for item in self.items.values():
            if item.title.lower() == title.lower():
                return item
        return None

    def list_with_filters(self, params):
        """Return a list of recipes matching the given search parameters."""
        result = list(self.items.values())

        if params.title:
            result = [item for item in result if params.title.lower() in item.title.lower()]

        if params.is_vegetarian is not None:
            result = [item for item in result if item.is_vegetarian == params.is_vegetarian]

        if params.servings is not None:
            result = [item for item in result if item.servings == params.servings]

        if params.instruction_text:
            result = [item for item in result if params.instruction_text.lower() in item.instructions.lower()]

        if params.include_ingredients:
            result = [
                item
                for item in result
                if all(
                    name in [part.ingredient.name for part in item.ingredients] for name in params.include_ingredients
                )
            ]

        if params.exclude_ingredients:
            result = [
                item
                for item in result
                if not any(
                    name in [part.ingredient.name for part in item.ingredients] for name in params.exclude_ingredients
                )
            ]

        return result

    def update(self, recipe, recipe_data):
        """Update the given recipe with any fields provided in the recipe_data (partial update)."""
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
            recipe.ingredients = [
                SimpleNamespace(ingredient=SimpleNamespace(name=name)) for name in update_data["ingredients"]
            ]
        self.items[recipe.id] = recipe
        return recipe

    def replace(self, recipe, recipe_data):
        """Replace all fields on the given recipe with the values from recipe_data (full update)."""
        recipe.title = recipe_data.title
        recipe.instructions = recipe_data.instructions
        recipe.servings = recipe_data.servings
        recipe.is_vegetarian = recipe_data.is_vegetarian
        recipe.ingredients = [
            SimpleNamespace(ingredient=SimpleNamespace(name=name)) for name in recipe_data.ingredients
        ]
        self.items[recipe.id] = recipe
        return recipe

    def delete(self, recipe):
        """Delete the given recipe from the repository."""
        self.items.pop(recipe.id, None)

    @staticmethod
    def _make_recipe(recipe_id, title, instructions, servings, is_vegetarian, ingredients):
        """Helper to create a recipe object with the expected structure for testing."""
        return SimpleNamespace(
            id=recipe_id,
            title=title,
            instructions=instructions,
            servings=servings,
            is_vegetarian=is_vegetarian,
            ingredients=[SimpleNamespace(ingredient=SimpleNamespace(name=name)) for name in ingredients],
        )


# --- Helpers ---


def _build_service():
    """Create a RecipeService backed by a fresh FakeRepository."""
    repo = FakeRepository()
    return RecipeService(repo), repo


def _seed_two_recipes(service):
    """Create Veg Curry (veg, 4 servings) and Salmon Tray Bake (non-veg, 2 servings)."""
    service.create_recipe(
        RecipeCreate(
            title="Veg Curry",
            instructions="Cook in oven",
            servings=4,
            is_vegetarian=True,
            ingredients=["potato", "carrot"],
        )
    )
    service.create_recipe(
        RecipeCreate(
            title="Salmon Tray Bake",
            instructions="Bake in oven",
            servings=2,
            is_vegetarian=False,
            ingredients=["salmon", "potato"],
        )
    )


# --- CREATE ---


def test_create_recipe_returns_structured_recipe():
    """Verify created recipe has correct id, title, and sorted ingredients."""
    service, _ = _build_service()

    result = service.create_recipe(
        RecipeCreate(
            title="Veg Curry",
            instructions="Cook in oven",
            servings=4,
            is_vegetarian=True,
            ingredients=["potato", "carrot"],
        )
    )

    assert result.id == 1
    assert result.title == "Veg Curry"
    assert result.ingredients == ["carrot", "potato"]


def test_create_recipe_raises_duplicate_for_same_title():
    """Reject creation when a recipe with the exact same title exists."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(title="Pasta", instructions="Boil", servings=2, is_vegetarian=True, ingredients=["pasta"])
    )

    with pytest.raises(RecipeDuplicateError, match="already exists"):
        service.create_recipe(
            RecipeCreate(title="Pasta", instructions="Bake", servings=4, is_vegetarian=False, ingredients=["flour"])
        )


def test_create_recipe_raises_duplicate_case_insensitive():
    """Reject creation when titles differ only in casing."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(title="Veg Curry", instructions="Cook", servings=2, is_vegetarian=True, ingredients=["potato"])
    )

    with pytest.raises(RecipeDuplicateError):
        service.create_recipe(
            RecipeCreate(title="VEG CURRY", instructions="Fry", servings=1, is_vegetarian=True, ingredients=["onion"])
        )


# --- GET ---


def test_get_recipe_returns_recipe():
    """Return the recipe when a valid ID is provided."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(
            title="Pasta", instructions="Boil pasta", servings=2, is_vegetarian=True, ingredients=["pasta", "tomato"]
        )
    )

    result = service.get_recipe(1)
    assert result.id == 1
    assert result.title == "Pasta"


def test_get_recipe_raises_not_found():
    """Raise RecipeNotFoundError for a non-existent ID."""
    service, _ = _build_service()
    with pytest.raises(RecipeNotFoundError):
        service.get_recipe(999)


# --- LIST ---


def test_list_recipes_returns_all_when_no_filters():
    """Return all recipes when no filters are applied."""
    service, _ = _build_service()
    _seed_two_recipes(service)

    result = service.list_recipes(RecipeSearchParams())
    assert result.total == 2
    assert len(result.items) == 2


def test_list_recipes_can_filter_by_multiple_fields():
    """Combine vegetarian, servings, ingredient, and instruction filters."""
    service, _ = _build_service()
    _seed_two_recipes(service)

    result = service.list_recipes(
        RecipeSearchParams(
            is_vegetarian=True,
            servings=4,
            include_ingredients=["potato"],
            exclude_ingredients=["salmon"],
            instruction_text="oven",
        )
    )

    assert result.total == 1
    assert result.items[0].title == "Veg Curry"


def test_list_recipes_filter_by_title():
    """Filter recipes by case-insensitive title substring."""
    service, _ = _build_service()
    _seed_two_recipes(service)

    result = service.list_recipes(RecipeSearchParams(title="salmon"))
    assert result.total == 1
    assert result.items[0].title == "Salmon Tray Bake"


def test_list_recipes_returns_empty_when_no_match():
    """Return empty list when no recipes match the filters."""
    service, _ = _build_service()
    _seed_two_recipes(service)

    result = service.list_recipes(RecipeSearchParams(title="pizza"))
    assert result.total == 0
    assert result.items == []


def test_list_recipes_pagination():
    """Verify limit/offset pagination returns correct slices and metadata."""
    service, _ = _build_service()
    _seed_two_recipes(service)

    page1 = service.list_recipes(RecipeSearchParams(), limit=1, offset=0)
    assert page1.total == 2
    assert len(page1.items) == 1
    assert page1.limit == 1
    assert page1.offset == 0

    page2 = service.list_recipes(RecipeSearchParams(), limit=1, offset=1)
    assert len(page2.items) == 1
    assert page2.offset == 1


# --- REPLACE (PUT) ---


def test_replace_recipe_replaces_all_fields():
    """Replace every field on an existing recipe via PUT."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(
            title="Old Title", instructions="Old instructions", servings=2, is_vegetarian=False, ingredients=["salt"]
        )
    )

    result = service.replace_recipe(
        1,
        RecipeReplace(
            title="New Title",
            instructions="New instructions",
            servings=8,
            is_vegetarian=True,
            ingredients=["pepper", "garlic"],
        ),
    )

    assert result.title == "New Title"
    assert result.instructions == "New instructions"
    assert result.servings == 8
    assert result.is_vegetarian is True
    assert result.ingredients == ["garlic", "pepper"]


def test_replace_recipe_raises_not_found():
    """Raise RecipeNotFoundError when replacing a non-existent recipe."""
    service, _ = _build_service()
    with pytest.raises(RecipeNotFoundError):
        service.replace_recipe(
            999,
            RecipeReplace(
                title="X", instructions="X", servings=1, is_vegetarian=False, ingredients=["x"]
            ),
        )


# --- UPDATE (PATCH) ---


def test_update_recipe_title_only():
    """Update only the title, leaving other fields unchanged."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(
            title="Old Title", instructions="Steps", servings=2, is_vegetarian=True, ingredients=["salt"]
        )
    )

    result = service.update_recipe(1, RecipeUpdate(title="New Title"))
    assert result.title == "New Title"
    assert result.instructions == "Steps"
    assert result.servings == 2


def test_update_recipe_ingredients_only():
    """Update only ingredients, leaving other fields unchanged."""
    service, _ = _build_service()
    service.create_recipe(
        RecipeCreate(
            title="Salad", instructions="Mix all", servings=1, is_vegetarian=True, ingredients=["lettuce"]
        )
    )

    result = service.update_recipe(1, RecipeUpdate(ingredients=["lettuce", "tomato", "cucumber"]))
    assert result.title == "Salad"
    assert result.ingredients == ["cucumber", "lettuce", "tomato"]


def test_update_recipe_raises_not_found():
    """Raise RecipeNotFoundError when patching a non-existent recipe."""
    service, _ = _build_service()
    with pytest.raises(RecipeNotFoundError):
        service.update_recipe(999, RecipeUpdate(title="Updated"))


# --- DELETE ---


def test_delete_recipe_removes_from_repository():
    """Delete a recipe and confirm it no longer exists."""
    service, repo = _build_service()
    service.create_recipe(
        RecipeCreate(
            title="To Delete", instructions="N/A", servings=1, is_vegetarian=False, ingredients=["salt"]
        )
    )

    service.delete_recipe(1)
    assert repo.get_by_id(1) is None


def test_delete_recipe_raises_not_found():
    """Raise RecipeNotFoundError when deleting a non-existent recipe."""
    service, _ = _build_service()
    with pytest.raises(RecipeNotFoundError):
        service.delete_recipe(999)


# --- SCHEMA VALIDATION ---


def test_create_recipe_strips_whitespace_and_deduplicates_ingredients():
    """Strip whitespace, lowercase, and deduplicate ingredients on create."""
    service, _ = _build_service()
    result = service.create_recipe(
        RecipeCreate(
            title="Test",
            instructions="Test",
            servings=1,
            is_vegetarian=False,
            ingredients=["  Salt  ", "salt", "SALT", "  pepper  "],
        )
    )
    assert result.ingredients == ["pepper", "salt"]


def test_create_recipe_rejects_empty_ingredients_after_strip():
    """Reject ingredients that become empty after stripping whitespace."""
    with pytest.raises(ValueError, match="At least one ingredient is required"):
        RecipeCreate(
            title="Test", instructions="Test", servings=1, is_vegetarian=False, ingredients=["   ", ""]
        )


def test_replace_rejects_empty_ingredients_after_strip():
    """Reject PUT payload with only whitespace ingredients."""
    with pytest.raises(ValueError, match="At least one ingredient is required"):
        RecipeReplace(
            title="Test", instructions="Test", servings=1, is_vegetarian=False, ingredients=["   ", ""]
        )


def test_update_rejects_empty_ingredients_after_strip():
    """Reject PATCH payload with only whitespace ingredients."""
    with pytest.raises(ValueError, match="At least one ingredient is required"):
        RecipeUpdate(ingredients=["   ", ""])


def test_update_allows_none_ingredients():
    """Allow omitting ingredients entirely in a PATCH payload."""
    schema = RecipeUpdate(title="Just title")
    assert schema.ingredients is None
