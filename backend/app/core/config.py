from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "BDXPostOffice API"
    API_V1_PREFIX: str = "/api/v1"
    RELEASE_ID: str = "dev-local"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/cam_feedback"
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 100
    STEP_VIEWER_CACHE_DIR: str = "./uploads/_step_cache"
    STEP_CONVERTER_COMMAND: str = ""

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"

    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = "ChangeMe123!"
    SYSTEM_BUILD_AUTOINCREMENT_ON_STARTUP: bool = False
    SYSTEM_BUILD_FORCE_INCREMENT: bool = False
    # format: "component:version;component:version"
    SYSTEM_BUILD_STARTUP_SPECS: str = "backend-api:0.1.0"
    AI_AGENT_ENABLED: bool = False
    AI_AGENT_PROVIDER: str = "openai_compatible"
    AI_AGENT_BASE_URL: str = "https://api.openai.com/v1/chat/completions"
    AI_AGENT_API_KEY: str | None = None
    AI_AGENT_MODEL: str = "gpt-4o-mini"
    AI_AGENT_TIMEOUT_SECONDS: int = 45

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
