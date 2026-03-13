"""Application configuration loaded from environment variables or .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Recipe API configuration settings."""

    app_name: str = "Recipe API"
    app_env: str = "local"
    app_debug: bool = True
    database_url: str = "postgresql+psycopg2://recipe_user:recipe_password@localhost:5432/recipe_db"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
