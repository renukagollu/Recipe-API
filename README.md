# Recipe API

Recipe management API built with FastAPI, PostgreSQL, and Alembic.

## Tech Stack

- **FastAPI** — REST API with auto-generated OpenAPI docs
- **PostgreSQL** — Relational database with normalized ingredient tables
- **SQLAlchemy 2.0** — ORM with repository pattern
- **Alembic** — Database migrations
- **Pydantic v2** — Request/response validation
- **Testcontainers** — Integration tests against real PostgreSQL
- **Docker Compose** — One-command local setup

## Features

- Full CRUD — `POST`, `GET`, `PUT` (replace), `PATCH` (partial update), `DELETE`
- Duplicate detection (case-insensitive title, returns 409)
- Filtering — title, vegetarian, servings, instruction text, include/exclude ingredients
- Pagination with `limit` and `offset`
- Consistent JSON response format with `success`, `data`, and `error` fields
- Structured JSON logging with request ID tracking

## Project Structure

```
app/
  api/routes/recipes.py    # HTTP endpoints
  services/                # Business logic
  repositories/            # Database queries
  schemas/                 # Pydantic models
  db/                      # SQLAlchemy models & session
  core/                    # Config, errors, logging, responses
  main.py                  # App entry point
alembic/                   # Database migrations
tests/
  unit/                    # Service + schema tests (FakeRepository)
  integration/             # Full API tests (Testcontainers)
```

## Quick Start (Docker Compose)

```bash
docker compose up --build -d
```

Open: http://localhost:8000/docs

## Quick Start (Local)

### 1. Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update `DATABASE_URL` in `.env` if your PostgreSQL credentials differ.

### 3. Start PostgreSQL

Use your local PostgreSQL or start only the database with Docker:

```bash
docker compose up db -d
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open: http://localhost:8000/docs

## Running Tests

**Prerequisites:** Docker must be running (Testcontainers needs it for integration tests).

```bash
# All tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

## API Endpoints

| Method   | Endpoint            | Description                  | Status |
|----------|---------------------|------------------------------|--------|
| `POST`   | `/recipes`          | Create a recipe              | 201    |
| `GET`    | `/recipes`          | List/filter recipes          | 200    |
| `GET`    | `/recipes/{id}`     | Get a recipe by ID           | 200    |
| `PUT`    | `/recipes/{id}`     | Replace a recipe (all fields)| 200    |
| `PATCH`  | `/recipes/{id}`     | Partial update               | 200    |
| `DELETE` | `/recipes/{id}`     | Delete a recipe              | 204    |
| `GET`    | `/health`           | Health check                 | 200    |

### POST /recipes — Create a recipe

All fields required. Ingredients are normalized (trimmed, lowercased, deduplicated).

```json
{
  "title": "Chicken Biryani",
  "instructions": "Marinate chicken, soak basmati rice and cook for 45 mins.",
  "servings": 5,
  "is_vegetarian": false,
  "ingredients": ["chicken", "basmati rice", "ghee", "salt", "whole spices"]
}
```

Returns `409` if a recipe with the same title already exists (case-insensitive).

### GET /recipes — List and filter recipes

All query parameters are optional. Returns paginated results.

| Parameter             | Type       | Description                              |
|-----------------------|------------|------------------------------------------|
| `title`               | string     | Case-insensitive substring match         |
| `is_vegetarian`       | boolean    | Filter by vegetarian status              |
| `servings`            | integer    | Filter by exact servings count           |
| `include_ingredients` | list[str]  | Recipes must contain all listed          |
| `exclude_ingredients` | list[str]  | Recipes must not contain any listed      |
| `instruction_text`    | string     | Case-insensitive instruction text search |
| `limit`               | integer    | Max results (default 10, max 100)        |
| `offset`              | integer    | Skip N results for pagination            |

### GET /recipes/{id} — Get a recipe by ID

Returns `404` if the recipe does not exist.

### PUT /recipes/{id} — Replace a recipe

All fields required (same body as POST). Completely replaces the existing recipe.

```json
{
  "title": "Updated Biryani",
  "instructions": "New instructions here.",
  "servings": 6,
  "is_vegetarian": false,
  "ingredients": ["chicken", "basmati rice", "saffron"]
}
```

Returns `422` if any required field is missing. Returns `404` if recipe not found.

### PATCH /recipes/{id} — Partial update

Only send the fields you want to change. Omitted fields remain unchanged.

```json
{
  "servings": 8,
  "ingredients": ["chicken", "basmati rice", "saffron", "fried onions"]
}
```

Returns `404` if recipe not found.

### DELETE /recipes/{id} — Delete a recipe

Returns `204 No Content` with empty body on success. Returns `404` if recipe not found.

### Response Format

All endpoints (except DELETE) return a consistent JSON structure with `success`, `message`, `data`, and `error` fields.

```json
{
  "success": true,
  "message": "Recipe created successfully",
  "data": {...},
  "error": null
}
```

Error responses follow the same structure:

```json
{
  "success": false,
  "message": "Recipe with title 'Chicken Biryani' already exists",
  "data": null,
  "error": {
    "code": "recipe_duplicate",
    "details": "Recipe with title 'Chicken Biryani' already exists"
  }
}
```

| Error Code          | Status | When                                    |
|---------------------|--------|-----------------------------------------|
| `validation_error`  | 422    | Missing or invalid request fields       |
| `recipe_not_found`  | 404    | Recipe ID does not exist                |
| `recipe_duplicate`  | 409    | Recipe with the same title exists       |
| `internal_error`    | 500    | Unexpected server error                 |
