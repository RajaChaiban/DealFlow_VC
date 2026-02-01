"""
Configuration management using Pydantic Settings.

Loads environment variables from .env file and provides
type-safe access to configuration values.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Settings
    app_name: str = Field(default="DealFlow AI Copilot", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")

    # Google AI
    google_api_key: str = Field(default="", description="Google Generative AI API key")

    # External APIs (optional)
    pitchbook_api_key: Optional[str] = Field(default=None, description="PitchBook API key")
    crunchbase_api_key: Optional[str] = Field(default=None, description="Crunchbase API key")
    serp_api_key: Optional[str] = Field(default=None, description="SERP API key")

    # File Storage
    upload_dir: str = Field(default="data/uploads", description="Upload directory")
    processed_dir: str = Field(default="data/processed", description="Processed files directory")
    output_dir: str = Field(default="data/outputs", description="Output directory")

    # Model Settings
    default_model: str = Field(
        default="gemini-1.5-pro-latest", description="Default Gemini model"
    )
    default_temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="Default temperature for AI responses"
    )
    max_tokens: int = Field(default=2048, ge=1, description="Maximum tokens for AI responses")

    # Database Settings
    database_url: str = Field(
        default="postgresql+asyncpg://dealflow:dealflow@localhost:5432/dealflow",
        description="PostgreSQL connection URL",
    )
    database_echo: bool = Field(default=False, description="Echo SQL statements")

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_ttl_seconds: int = Field(default=3600, description="Default cache TTL in seconds")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dealflow-secret-key-change-in-production",
        description="Secret key for JWT encoding",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=60, description="Access token expiration in minutes"
    )

    # API Key Authentication
    api_keys: str = Field(
        default="",
        description="Comma-separated list of valid API keys",
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=30, description="Rate limit: requests per minute"
    )
    rate_limit_per_hour: int = Field(
        default=200, description="Rate limit: requests per hour"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8501",
        description="Comma-separated allowed CORS origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir)

    @property
    def processed_path(self) -> Path:
        """Get processed directory as Path object."""
        return Path(self.processed_dir)

    @property
    def output_path(self) -> Path:
        """Get output directory as Path object."""
        return Path(self.output_dir)

    @property
    def cors_origin_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if not self.cors_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def api_key_list(self) -> list[str]:
        """Get API keys as a list."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    def get_data_directories(self) -> list[Path]:
        """Get all data directories that should be created on startup."""
        return [
            self.upload_path,
            self.processed_path,
            self.output_path,
            Path("logs"),
        ]


# Global settings instance
settings = Settings()
