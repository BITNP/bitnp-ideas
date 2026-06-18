from pathlib import Path

import pytest

from bitnp_ideas.core.config import ConfigError, parse_settings_file


def test_config_uses_requested_postgres_url() -> None:
    settings = parse_settings_file(Path("config.yaml"))

    assert settings.database.url == "postgres://bitnp_ideas:bitnp_ideas@127.0.0.1/bitnp_ideas"
    assert (
        settings.database.sqlalchemy_url
        == "postgresql+psycopg://bitnp_ideas:bitnp_ideas@127.0.0.1/bitnp_ideas"
    )
    assert settings.security.session_token_ttl_seconds == 28800
    assert settings.security.oidc_state_ttl_seconds == 600


def test_invalid_config_is_rejected_without_defaults(tmp_path: Path) -> None:
    invalid_config = tmp_path / "config.yaml"
    invalid_config.write_text(
        """
app:
  name: BITNP IDEAS
database:
  url: sqlite:///local.db
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        parse_settings_file(invalid_config)
