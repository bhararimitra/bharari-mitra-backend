"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "BharariMitra API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bharari:bharari@localhost:5432/bhararimitradb"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis (optional in local dev — API works without it)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # CORS
    CORS_ORIGINS: list[str] = ["https://bhararimitra.in", "http://localhost:3000"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Scheduler
    CRAWLER_INTERVAL_HOURS: int = 6
    CRAWLER_RUN_ON_STARTUP: bool = True
    # Keep False when using scripts/crawler_worker.py (avoid double crawls)
    ENABLE_API_SCHEDULER: bool = False
    # Weekly expired-job cleanup (Sunday 02:00 UTC via crawler worker)
    JOB_CLEANUP_ENABLED: bool = True
    JOB_CLEANUP_RETENTION_DAYS: int = 7

    # IndexNow — public key file must be at https://bhararimitra.in/{key}.txt
    INDEXNOW_KEY: str = ""

    # Security
    SECRET_KEY: str = "change-this-in-production"
    API_RATE_LIMIT: str = "100/minute"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
