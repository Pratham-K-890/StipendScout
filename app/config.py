from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""
    openrouter_api_key: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    github_token: str = ""
    # Comma-separated. Defaults cover local dev (Vite's default port); a
    # deployed frontend on a real domain needs this set in .env or every
    # request gets CORS-blocked — this was hardcoded before and would have
    # silently broken the first real deployment.
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3_driver(cls, v: str) -> str:
        # Neon hands out plain "postgresql://", which SQLAlchemy maps to
        # psycopg2 by default. We install psycopg (v3) instead, so force it.
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v


settings = Settings()
