from functools import cached_property

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BITNP IDEAS"
    database_url: str = "postgresql+psycopg://bitnp:bitnp_dev_password@localhost:5432/bitnp_ideas"
    backend_cors_origins: str = "http://localhost:5173"
    session_secret_key: str = "change-me"
    oidc_issuer_url: AnyHttpUrl | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    api_key_timestamp_tolerance_seconds: int = 300
    api_key_allowed_entities: list[str] = Field(default_factory=lambda: ["idea"])

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
