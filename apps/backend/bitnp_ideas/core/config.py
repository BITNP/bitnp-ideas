from os import environ
from pathlib import Path
from sys import stderr
from typing import Self

import yaml
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)


class ConfigError(ValueError):
    pass


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    openapi_url: str = Field(pattern=r"^/")
    docs_url: str = Field(pattern=r"^/")


class ServerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cors_origins: list[AnyHttpUrl] = Field(min_length=1)

    @computed_field
    @property
    def cors_origin_strings(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.cors_origins]


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
            return value

        raise ValueError(
            "database.url must use postgres://, postgresql://, or postgresql+psycopg://"
        )

    @computed_field
    @property
    def sqlalchemy_url(self) -> str:
        if self.url.startswith("postgres://"):
            return self.url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.url.startswith("postgresql://"):
            return self.url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.url


class OidcSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    issuer_url: AnyHttpUrl | None
    client_id: str | None
    client_secret: str | None

    @model_validator(mode="after")
    def validate_enabled_provider(self) -> Self:
        if self.enabled and (not self.issuer_url or not self.client_id or not self.client_secret):
            raise ValueError(
                "oidc.issuer_url, oidc.client_id, and oidc.client_secret are required "
                "when oidc.enabled is true"
            )
        return self


class SecuritySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_secret_key: str = Field(min_length=16)
    oidc: OidcSettings


class ApiKeySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp_tolerance_seconds: int = Field(gt=0, le=3600)
    allowed_entities: list[str] = Field(min_length=1)

    @field_validator("allowed_entities")
    @classmethod
    def validate_allowed_entities(cls, value: list[str]) -> list[str]:
        if value != ["idea"]:
            raise ValueError("api_keys.allowed_entities must be exactly ['idea'] in v1")
        return value


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSettings
    server: ServerSettings
    database: DatabaseSettings
    security: SecuritySettings
    api_keys: ApiKeySettings


def default_config_path() -> Path:
    configured_path = environ.get("BITNP_IDEAS_CONFIG")
    if configured_path:
        return Path(configured_path).expanduser().resolve()

    return Path(__file__).resolve().parents[2] / "config.yaml"


def parse_settings_file(path: Path) -> Settings:
    if not path.exists():
        raise ConfigError(f"Backend config file does not exist: {path}")
    if not path.is_file():
        raise ConfigError(f"Backend config path is not a file: {path}")

    try:
        raw_config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Backend config YAML is invalid: {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Backend config file cannot be read: {path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ConfigError("Backend config YAML root must be an object")

    try:
        return Settings.model_validate(raw_config)
    except ValidationError as exc:
        raise ConfigError(f"Backend config validation failed: {exc}") from exc


def load_settings_or_exit(path: Path | None = None) -> Settings:
    config_path = path or default_config_path()
    try:
        return parse_settings_file(config_path)
    except ConfigError as exc:
        print(f"Fatal backend configuration error: {exc}", file=stderr)
        raise SystemExit(78) from exc


settings = load_settings_or_exit()
