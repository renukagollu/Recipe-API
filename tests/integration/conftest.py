"""Integration test fixtures using testcontainers for a real PostgreSQL database."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    """Start a disposable PostgreSQL 16 container for the test session."""
    container = PostgresContainer("postgres:16")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def migrated_database(postgres_container):
    """Run Alembic migrations against the testcontainer and return the database URL."""
    database_url = postgres_container.get_connection_url().replace("postgresql://", "postgresql+psycopg2://")
    os.environ["DATABASE_URL"] = database_url

    project_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

    command.upgrade(alembic_cfg, "head")
    return database_url


@pytest.fixture(scope="session")
def test_engine(migrated_database):
    """Create a SQLAlchemy engine bound to the testcontainer database."""
    engine = create_engine(migrated_database, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create a session factory bound to the test engine."""
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session")
def app_with_test_db(test_session_factory):
    """Override FastAPI's get_db dependency to use the test session factory."""
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        """Yield a test database session."""
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
async def api_client(app_with_test_db):
    """Provide an async HTTP client wired to the test application."""
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        yield client


@pytest.fixture(autouse=True)
def clear_tables(app_with_test_db, test_session_factory):
    """Delete all rows from tables before each test for isolation."""
    db = test_session_factory()
    try:
        db.execute(text("DELETE FROM recipe_ingredients"))
        db.execute(text("DELETE FROM ingredients"))
        db.execute(text("DELETE FROM recipes"))
        db.commit()
        yield
    finally:
        db.close()
