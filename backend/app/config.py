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

    # Supabase Configuration
    supabase_project_id: str = ""
    supabase_api_key: str = ""
    supabase_data_url: str = ""  # Direct database connection URL
    supabase_pooler_url: str = ""  # Transaction pooler URL (port 6543)
    supabase_ssl_mode: str = "require"  # SSL mode for Supabase connections

    # Storage Provider (s3, uploadthing, or supabase)
    storage_provider: Literal["s3", "uploadthing", "supabase"] = "uploadthing"

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
    app_url: str = "https://nova-vat.com"  # Base URL for email links
    debug: bool = False

    # Email/SMTP Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Nova VAT Assistant"
    smtp_use_tls: bool = True

    def get_database_url(self) -> str:
        """Get SQLAlchemy database URL (PostgreSQL or SQLite fallback).
        
        Priority:
        1. SUPABASE_DATA_URL (direct Supabase PostgreSQL connection - must start with postgres://)
        2. DATABASE_URL (explicit PostgreSQL URL)
        3. DATABASE_PATH (if it's a PostgreSQL URL)
        4. SQLite fallback
        
        Note: SUPABASE_DATA_URL should be the PostgreSQL connection string from Supabase,
        NOT the REST API URL. Get it from: Supabase Dashboard > Settings > Database > Connection string
        """
        # Supabase direct connection takes priority (only if it's a postgres URL)
        if self.supabase_data_url and self.supabase_data_url.startswith(("postgres://", "postgresql://")):
            url = self.supabase_data_url
            # Ensure postgresql:// prefix (not postgres://)
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        
        # Check DATABASE_URL
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        
        # Check if DATABASE_PATH contains a PostgreSQL URL
        if self.database_path.startswith(("postgresql://", "postgres://")):
            url = self.database_path
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        
        # Default to SQLite
        return f"sqlite:///{self.database_path}"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        db_url = self.get_database_url()
        return db_url.startswith("sqlite")

    @property
    def is_supabase(self) -> bool:
        """Check if using Supabase database."""
        # Only consider it Supabase if we have a valid PostgreSQL connection URL
        if self.supabase_data_url and self.supabase_data_url.startswith(("postgres://", "postgresql://")):
            return True
        # Or if we have a database URL that points to supabase pooler
        db_url = self.get_database_url()
        return "supabase.com" in db_url or "pooler.supabase.com" in db_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
