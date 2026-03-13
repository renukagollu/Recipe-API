"""FastAPI application entry point with middleware and exception handlers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.api.routes.recipes import router as recipe_router
from app.core.config import settings
from app.core.errors import RecipeDuplicateError, RecipeNotFoundError
from app.core.logging import RequestLogMiddleware, setup_logging
from app.core.responses import error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize logging on application startup."""
    setup_logging()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Recipe management API .",
    lifespan=lifespan,
)

app.add_middleware(RequestLogMiddleware)
app.include_router(recipe_router)


@app.get("/health")
def health_check():
    """Return service health status."""
    return {
        "success": True,
        "message": "Service is healthy",
        "data": {"status": "ok"},
        "error": None,
    }


@app.exception_handler(RecipeNotFoundError)
async def recipe_not_found_handler(request: Request, exc: RecipeNotFoundError):
    """Return a 404 response when a recipe is not found."""
    return error_response(str(exc), "recipe_not_found", 404)


@app.exception_handler(RecipeDuplicateError)
async def recipe_duplicate_handler(request: Request, exc: RecipeDuplicateError):
    """Return a 409 response when a recipe with the same title already exists."""
    return error_response(str(exc), "recipe_duplicate", 409)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a 422 response with the first validation error detail."""
    first_error = exc.errors()[0]
    detail_message = f"{'.'.join([str(item) for item in first_error['loc']])}: {first_error['msg']}"
    return error_response(detail_message, "validation_error", 422)
