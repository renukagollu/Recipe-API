"""Integration tests for Recipe API endpoints using testcontainers PostgreSQL."""

import pytest


# --- Helper ---

RECIPE_PAYLOAD = {
    "title": "Veg Potato Bake",
    "instructions": "Put potatoes in oven for 30 minutes",
    "servings": 4,
    "is_vegetarian": True,
    "ingredients": ["potato", "olive oil", "salt"],
}


async def _create_recipe(api_client, **overrides):
    """Create a recipe with defaults, applying any overrides."""
    payload = {**RECIPE_PAYLOAD, **overrides}
    response = await api_client.post("/recipes", json=payload)
    return response


# --- POST /recipes ---


async def test_create_recipe_success(api_client):
    """Create a valid recipe and verify 201 with correct body."""
    response = await _create_recipe(api_client)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Veg Potato Bake"
    assert body["message"] == "Recipe created successfully"


async def test_create_recipe_validation_error_missing_fields(api_client):
    """Return 422 when required fields are missing."""
    response = await api_client.post("/recipes", json={"title": "Only title"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"


async def test_create_recipe_duplicate_title_returns_409(api_client):
    """Return 409 when creating a recipe with an existing title."""
    await _create_recipe(api_client, title="Veg Curry")
    response = await _create_recipe(api_client, title="Veg Curry")
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "recipe_duplicate"


async def test_create_recipe_duplicate_title_case_insensitive(api_client):
    """Return 409 for duplicate titles differing only in casing."""
    await _create_recipe(api_client, title="Chicken Biryani")
    response = await _create_recipe(api_client, title="CHICKEN BIRYANI")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "recipe_duplicate"


async def test_create_recipe_deduplicates_ingredients(api_client):
    """Deduplicate and normalize ingredient list on creation."""
    response = await _create_recipe(api_client, ingredients=["Salt", "  salt ", "SALT", "pepper"])
    assert response.status_code == 201
    ingredients = response.json()["data"]["ingredients"]
    assert ingredients.count("salt") == 1
    assert "pepper" in ingredients


# --- GET /recipes ---


async def test_list_recipes_returns_all(api_client):
    """Return all recipes when no filters are applied."""
    await _create_recipe(api_client, title="Recipe A")
    await _create_recipe(api_client, title="Recipe B")

    response = await api_client.get("/recipes")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 2


async def test_list_recipes_filter_by_title(api_client):
    """Filter recipes by case-insensitive title substring."""
    await _create_recipe(api_client, title="Chicken Biryani")
    await _create_recipe(api_client, title="Veg Curry")

    response = await api_client.get("/recipes", params={"title": "biryani"})
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["title"] == "Chicken Biryani"


async def test_list_recipes_filter_by_vegetarian(api_client):
    """Filter recipes by vegetarian status."""
    await _create_recipe(api_client, title="Veg A", is_vegetarian=True)
    await _create_recipe(api_client, title="Non-Veg B", is_vegetarian=False)

    response = await api_client.get("/recipes", params={"is_vegetarian": "true"})
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["title"] == "Veg A"


async def test_list_recipes_filter_by_servings(api_client):
    """Filter recipes by exact servings count."""
    await _create_recipe(api_client, title="Small", servings=2)
    await _create_recipe(api_client, title="Large", servings=8)

    response = await api_client.get("/recipes", params={"servings": 2})
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["title"] == "Small"


async def test_list_recipes_include_and_exclude_ingredients(api_client):
    """Include recipes with potato but exclude those with salmon."""
    await _create_recipe(api_client, title="Salmon Bake", is_vegetarian=False, ingredients=["salmon", "potato"])
    await _create_recipe(api_client, title="Veg Roast", is_vegetarian=True, ingredients=["potato", "carrot"])

    response = await api_client.get(
        "/recipes",
        params={"include_ingredients": ["potato"], "exclude_ingredients": ["salmon"]},
    )
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["title"] == "Veg Roast"


async def test_list_recipes_pagination(api_client):
    """Verify limit/offset pagination returns correct slices."""
    await _create_recipe(api_client, title="Recipe 1")
    await _create_recipe(api_client, title="Recipe 2")
    await _create_recipe(api_client, title="Recipe 3")

    response = await api_client.get("/recipes", params={"limit": 2, "offset": 0})
    body = response.json()
    assert body["data"]["total"] == 3
    assert len(body["data"]["items"]) == 2
    assert body["data"]["limit"] == 2
    assert body["data"]["offset"] == 0

    response2 = await api_client.get("/recipes", params={"limit": 2, "offset": 2})
    body2 = response2.json()
    assert len(body2["data"]["items"]) == 1
    assert body2["data"]["offset"] == 2


async def test_list_recipes_filter_by_instruction_text(api_client):
    """Filter recipes by case-insensitive instruction text match."""
    await _create_recipe(api_client, title="Baked", instructions="Bake in oven for 30 mins")
    await _create_recipe(api_client, title="Fried", instructions="Fry in a pan")

    response = await api_client.get("/recipes", params={"instruction_text": "oven"})
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["title"] == "Baked"


# --- GET /recipes/{id} ---


async def test_get_recipe_by_id_success(api_client):
    """Retrieve a recipe by its ID."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Veg Potato Bake"


async def test_get_recipe_by_id_not_found(api_client):
    """Return 404 for a non-existent recipe ID."""
    response = await api_client.get("/recipes/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "recipe_not_found"


# --- PUT /recipes/{id} (full replace) ---


async def test_put_replace_recipe_success(api_client):
    """Replace all fields of an existing recipe via PUT."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    replace_payload = {
        "title": "Completely New Recipe",
        "instructions": "Brand new instructions",
        "servings": 10,
        "is_vegetarian": False,
        "ingredients": ["chicken", "rice"],
    }
    response = await api_client.put(f"/recipes/{recipe_id}", json=replace_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Recipe replaced successfully"
    assert body["data"]["title"] == "Completely New Recipe"
    assert body["data"]["servings"] == 10
    assert body["data"]["is_vegetarian"] is False
    assert set(body["data"]["ingredients"]) == {"chicken", "rice"}


async def test_put_replace_recipe_missing_fields_returns_422(api_client):
    """Return 422 when PUT payload is missing required fields."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.put(f"/recipes/{recipe_id}", json={"title": "Partial Only"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"


async def test_put_replace_recipe_not_found(api_client):
    """Return 404 when replacing a non-existent recipe."""
    replace_payload = {
        "title": "Ghost Recipe",
        "instructions": "Does not exist",
        "servings": 1,
        "is_vegetarian": False,
        "ingredients": ["air"],
    }
    response = await api_client.put("/recipes/99999", json=replace_payload)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


# --- PATCH /recipes/{id} (partial update) ---


async def test_patch_update_title_only(api_client):
    """Update only the title via PATCH, leaving other fields unchanged."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.patch(f"/recipes/{recipe_id}", json={"title": "Updated Title"})
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Recipe updated successfully"
    assert body["data"]["title"] == "Updated Title"
    assert body["data"]["servings"] == 4  # unchanged


async def test_patch_update_ingredients_only(api_client):
    """Update only ingredients via PATCH, leaving other fields unchanged."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.patch(f"/recipes/{recipe_id}", json={"ingredients": ["new ingredient"]})
    assert response.status_code == 200
    assert response.json()["data"]["ingredients"] == ["new ingredient"]
    assert response.json()["data"]["title"] == "Veg Potato Bake"  # unchanged


async def test_patch_update_multiple_fields(api_client):
    """Update several fields at once via PATCH."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.patch(
        f"/recipes/{recipe_id}",
        json={"instructions": "New instructions", "servings": 8, "is_vegetarian": False},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["instructions"] == "New instructions"
    assert data["servings"] == 8
    assert data["is_vegetarian"] is False
    assert data["title"] == "Veg Potato Bake"  # unchanged


async def test_patch_update_recipe_not_found(api_client):
    """Return 404 when patching a non-existent recipe."""
    response = await api_client.patch("/recipes/99999", json={"title": "Nope"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


# --- DELETE /recipes/{id} ---


async def test_delete_recipe_success(api_client):
    """Delete a recipe and verify 204 No Content, then confirm 404 on GET."""
    create_resp = await _create_recipe(api_client)
    recipe_id = create_resp.json()["data"]["id"]

    response = await api_client.delete(f"/recipes/{recipe_id}")
    assert response.status_code == 204
    assert response.content == b""

    get_resp = await api_client.get(f"/recipes/{recipe_id}")
    assert get_resp.status_code == 404


async def test_delete_recipe_not_found(api_client):
    """Return 404 when deleting a non-existent recipe."""
    response = await api_client.delete("/recipes/99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


# --- Health check ---


async def test_health_check(api_client):
    """Verify /health returns 200 with status ok."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
