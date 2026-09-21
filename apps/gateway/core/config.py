import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "CRouter"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./crouter.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_FALLBACK_IN_MEMORY: bool = True

    MOCK_PROVIDER_URL: str = "http://localhost:8001"
    MOCK_PROVIDER_PORT: int = 8001

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEYS: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_API_KEYS: Optional[str] = None
    COMMANDCODE_API_KEY: Optional[str] = None
    COMMANDCODE_API_KEYS: Optional[str] = None
    COMMANDCODE_BASE_URL: str = "https://api.commandcode.ai/provider/v1"

    DEFAULT_RATE_LIMIT_RPM: int = 60
    DEFAULT_MAX_CONCURRENCY: int = 10
    DEFAULT_REQUEST_TIMEOUT_MS: int = 15000

    BREAKER_FAILURE_THRESHOLD: int = 5
    BREAKER_COOLDOWN_SECONDS: int = 30


settings = Settings()
