"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database - supports PostgreSQL URL or SQLite path
    database_url: str | None = None  # e.g., postgresql://user:pass@host:5432/dbname
    database_path: str = "./data/nova.db"  # can be SQLite path OR PostgreSQL URL

    # Storage Provider (s3 or uploadthing)
    storage_provider: Literal["s3", "uploadthing"] = "uploadthing"

    # AWS S3 (if storage_provider is s3)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "eu-west-2"
    s3_bucket_name: str = "nova-vat-documents"

    # UploadThing (if storage_provider is uploadthing)
    uploadthing_token: str = ""

    # AI Provider
    ai_provider: Literal["openai", "anthropic"] = "anthropic"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Application
    app_name: str = "Nova VAT Readiness Tool"
    debug: bool = False

    def get_database_url(self) -> str:
        """Get SQLAlchemy database URL (PostgreSQL or SQLite fallback)."""
        # Check DATABASE_URL first
        if self.database_url:
            return self.database_url
        # Check if DATABASE_PATH contains a PostgreSQL URL
        if self.database_path.startswith(("postgresql://", "postgres://")):
            return self.database_path
        # Default to SQLite
        return f"sqlite:///{self.database_path}"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        db_url = self.get_database_url()
        return db_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
