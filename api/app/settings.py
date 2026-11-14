"""Application settings, loaded once from the environment.

The model is frozen (immutable) and validated eagerly: misconfiguration
(such as a missing or empty ``API_KEYS``) fails at startup, never at
request time, and the app can never run with auth turned off.
"""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_api_keys(raw: str) -> tuple[str, ...]:
    """Split a comma-separated ``API_KEYS`` value into individual keys."""
    return tuple(key.strip() for key in raw.split(",") if key.strip())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # API config from .env, database credentials from the repo-root
        # .env.db (BE-002): a single source of truth, both gitignored.
        env_file=(".env", "../.env.db"),
        frozen=True,
        extra="ignore",
    )

    api_keys: str = ""
    app_version: str = "0.1.0"

    postgres_user: str = "todo_agent"
    postgres_password: SecretStr = SecretStr("")
    postgres_db: str = "todo_agent"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    @field_validator("api_keys")
    @classmethod
    def _must_have_at_least_one_key(cls, value: str) -> str:
        if not parse_api_keys(value):
            raise ValueError("API_KEYS must define at least one API key")
        return value

    @property
    def database_url(self) -> str:
        """Derived async DSN. Never log or print it (it embeds the password)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance (built once, then frozen)."""
    return Settings()
