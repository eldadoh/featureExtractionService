"""
Configuration management using Pydantic Settings.
Centralizes all environment variables and configuration.

Environment Variables:
    REDIS_HOST: Redis server hostname (default: redis)
    REDIS_PORT: Redis server port (default: 6379)
    API_HOST: API server host (default: 0.0.0.0)
    API_PORT: API server port (default: 8000)
    WORKERS: Number of Uvicorn workers (default: 4)
    CACHE_TTL: Cache time-to-live in seconds (default: 3600)
    MAX_IMAGE_SIZE_MB: Maximum image size in MB (default: 10)
    LOG_LEVEL: Logging level (default: INFO)
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    All settings can be overridden via environment variables.
    Follows 12-factor app principles.
    """
    
    # Redis Configuration
    redis_host: str = Field(default="redis", description="Redis hostname")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_password: str | None = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, ge=1, description="Redis connection pool size")
    
    # Cache Configuration
    cache_ttl: int = Field(default=3600, ge=60, description="Cache TTL in seconds")
    cache_enabled: bool = Field(default=True, description="Enable/disable caching")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    api_workers: int = Field(default=4, ge=1, le=16, description="Number of workers")
    
    # Feature Detector Configuration
    feature_detector_workers: int = Field(default=4, ge=1, le=16, description="Thread pool size")
    warmup_timeout: int = Field(default=10, ge=5, le=60, description="Warmup timeout in seconds")
    
    # Image Processing Configuration
    max_image_size_mb: int = Field(default=10, ge=1, le=100, description="Max image size in MB")
    allowed_extensions: set[str] = Field(
        default={"jpg", "jpeg", "png", "bmp", "tif", "tiff"},
        description="Allowed image extensions"
    )
    upload_dir: str = Field(default="/app/data/uploads", description="Upload directory")
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "console"] = Field(default="json", description="Log format")
    
    # Application Metadata
    app_name: str = Field(default="Feature Detection API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Environment"
    )
    
    # Rate Limiting (optional future enhancement)
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, description="Requests per minute")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("max_image_size_mb")
    @classmethod
    def validate_image_size(cls, v: int) -> int:
        """Validate max image size is reasonable."""
        if v > 100:
            raise ValueError("max_image_size_mb cannot exceed 100 MB")
        return v
    
    @property
    def max_image_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_image_size_mb * 1024 * 1024
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = Settings()

