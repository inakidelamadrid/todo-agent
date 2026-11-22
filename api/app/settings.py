"""Application settings, loaded once from the environment.

The model is frozen (immutable) and validated eagerly: misconfiguration
(such as a missing or empty ``API_KEYS``) fails at startup, never at
request time, and the app can never run with auth turned off.
"""

import re
from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Telegram allows 1-256 of these characters; we require at least 16.
_WEBHOOK_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,256}$")


def parse_api_keys(raw: str) -> tuple[str, ...]:
    """Split a comma-separated ``API_KEYS`` value into individual keys."""
    return tuple(key.strip() for key in raw.split(",") if key.strip())


def parse_csv(raw: str) -> tuple[str, ...]:
    """Split a comma-separated env value: trim, drop empties."""
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def normalize_pem(raw: str) -> str:
    """Turn escaped ``\\n`` into real newlines (PEM on one .env line) and trim."""
    return raw.strip().replace("\\n", "\n")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # API config from .env, database credentials from the repo-root
        # .env.db (BE-002): a single source of truth, both gitignored.
        env_file=(".env", "../.env.db"),
        frozen=True,
        extra="ignore",
        # Never echo offending values (often secrets) in validation errors.
        hide_input_in_errors=True,
    )

    api_keys: str = ""
    app_version: str = "0.1.0"

    postgres_user: str = "todo_agent"
    postgres_password: SecretStr = SecretStr("")
    postgres_db: str = "todo_agent"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    telegram_bot_token: SecretStr = SecretStr("")
    telegram_webhook_secret: SecretStr = SecretStr("")
    telegram_allowed_user_id: int | None = None

    clerk_jwt_public_key: str = ""
    clerk_authorized_parties: str = ""
    clerk_allowed_user_ids: str = ""
    admin_user_ids: str = ""  # optional; empty means no admin exists

    @field_validator("api_keys")
    @classmethod
    def _must_have_at_least_one_key(cls, value: str) -> str:
        if not parse_api_keys(value):
            raise ValueError("API_KEYS must define at least one API key")
        return value

    @field_validator("telegram_webhook_secret")
    @classmethod
    def _webhook_secret_must_be_strong(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        # Empty is allowed (Telegram integration is optional); a set value
        # must be strong enough to guard the webhook endpoint. The error
        # message intentionally never echoes the value.
        if raw and not _WEBHOOK_SECRET_PATTERN.fullmatch(raw):
            raise ValueError(
                "TELEGRAM_WEBHOOK_SECRET must be 16-256 characters of A-Z a-z 0-9 _ -"
            )
        return value

    @property
    def database_url(self) -> str:
        """Derived async DSN. Never log or print it (it embeds the password)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def telegram_enabled(settings: Settings) -> bool:
    """True only when the full Telegram configuration is present.

    Later dependencies use this to fail closed: unset means deny.
    """
    return bool(
        settings.telegram_bot_token.get_secret_value()
        and settings.telegram_webhook_secret.get_secret_value()
        and settings.telegram_allowed_user_id is not None
    )


def clerk_enabled(settings: Settings) -> bool:
    """True only when all three Clerk values are configured; unset means deny."""
    return bool(
        normalize_pem(settings.clerk_jwt_public_key)
        and parse_csv(settings.clerk_authorized_parties)
        and parse_csv(settings.clerk_allowed_user_ids)
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance (built once, then frozen)."""
    return Settings()
