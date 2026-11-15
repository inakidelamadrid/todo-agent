"""Settings for the Telegram integration (BE-004): secrets stay secrets.

All constructions use ``_env_file=None`` so tests never read the developer's
real ``api/.env`` — real tokens must never appear in test output.
"""

import pytest
from pydantic import ValidationError

from app.settings import Settings, telegram_enabled

FIELDS = {
    "telegram_bot_token": "123:abc",
    "telegram_webhook_secret": "a" * 32,
    "telegram_allowed_user_id": 42,
}


def _settings(**overrides):
    return Settings(_env_file=None, **{**FIELDS, **overrides})


def test_app_starts_without_telegram_settings() -> None:
    settings = Settings(_env_file=None)
    assert settings.telegram_bot_token.get_secret_value() == ""
    assert settings.telegram_webhook_secret.get_secret_value() == ""
    assert settings.telegram_allowed_user_id is None
    assert telegram_enabled(settings) is False


@pytest.mark.parametrize("missing", list(FIELDS))
def test_telegram_enabled_needs_all_three(missing: str) -> None:
    absent = {"telegram_bot_token": "", "telegram_webhook_secret": "", "telegram_allowed_user_id": None}
    assert telegram_enabled(Settings(_env_file=None, **{**FIELDS, missing: absent[missing]})) is False


def test_telegram_enabled_when_all_set() -> None:
    assert _settings() and telegram_enabled(_settings()) is True


def test_short_webhook_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="16-256 characters"):
        _settings(telegram_webhook_secret="a" * 15)

    # The boundary values are accepted.
    assert _settings(telegram_webhook_secret="a" * 16)
    assert _settings(telegram_webhook_secret="a" * 256)

    # And empty stays allowed.
    assert Settings(_env_file=None).telegram_webhook_secret.get_secret_value() == ""


def test_webhook_secret_with_bad_characters_is_rejected() -> None:
    bad = "a" * 16 + "!"
    with pytest.raises(ValidationError, match="16-256 characters") as exc_info:
        _settings(telegram_webhook_secret=bad)
    # The error text must not echo the bad value.
    assert bad not in str(exc_info.value)


def test_secrets_do_not_appear_in_repr() -> None:
    token, secret = "123:abc-token", "s3cr3t-webhook-value"
    settings = Settings(
        _env_file=None, telegram_bot_token=token, telegram_webhook_secret=secret
    )
    text = repr(settings)
    assert token not in text
    assert secret not in text
