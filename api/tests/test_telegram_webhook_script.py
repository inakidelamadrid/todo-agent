"""Tests for the telegram_webhook CLI script (host-only output, guarded ops)."""

import asyncio
import datetime

import pytest
from aiogram.types import WebhookInfo

from app.settings import Settings
from scripts import telegram_webhook as tw

FAKE_TOKEN = "000000:FAKE-TEST-TOKEN"
FAKE_SECRET = "fake-test-secret-0000"

SETTINGS = Settings(
    _env_file=None,
    telegram_bot_token=FAKE_TOKEN,
    telegram_webhook_secret=FAKE_SECRET,
)


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class _FakeBot:
    """Records how it was built and called; performs no network I/O."""

    instances: list["_FakeBot"] = []

    def __init__(self, token: str):
        self.token = token
        self.calls: list[tuple[str, dict]] = []
        self.session = _FakeSession()
        _FakeBot.instances.append(self)

    async def set_webhook(self, url: str, **kwargs) -> bool:
        self.calls.append((url, kwargs))
        return True


def _run_set_with_fake_bot(monkeypatch: pytest.MonkeyPatch, **kwargs) -> str:
    _FakeBot.instances = []
    monkeypatch.setattr(tw, "Bot", _FakeBot)
    return asyncio.run(tw._run_set(kwargs["settings"], kwargs["url"]))


def _info(**overrides) -> WebhookInfo:
    base = {
        # Realistic adversarial case: the URL path and error text contain
        # our own secret values; the formatter must not echo any of it.
        "url": f"https://abc123.ngrok.app{tw.WEBHOOK_PATH}/{FAKE_SECRET}?token={FAKE_TOKEN}",
        "has_custom_certificate": False,
        "pending_update_count": 3,
        "last_error_date": datetime.datetime(2026, 11, 12, 10, 0),
        "last_error_message": f"wrong response mentioning {FAKE_SECRET}",
        "allowed_updates": ["message", "callback_query"],
    }
    return WebhookInfo(**{**base, **overrides})


def test_format_webhook_info_shows_host_pending_and_last_error() -> None:
    out = tw.format_webhook_info(_info())
    assert "abc123.ngrok.app" in out
    assert "pending updates: 3" in out
    assert "last error: 2026-11-12" in out
    assert "allowed updates: message, callback_query" in out


def test_format_webhook_info_never_contains_secret_or_token() -> None:
    out = tw.format_webhook_info(_info(), redact=(FAKE_TOKEN, FAKE_SECRET))
    assert FAKE_SECRET not in out
    assert FAKE_TOKEN not in out
    assert tw.WEBHOOK_PATH not in out  # host only, never the path
    # Redacted occurrences are visibly blanked, not silently kept.
    assert "***" in out


def test_format_webhook_info_without_error() -> None:
    out = tw.format_webhook_info(_info(last_error_date=None, last_error_message=None))
    assert "last error: (none)" in out


def test_set_rejects_http_url() -> None:
    with pytest.raises(SystemExit, match="https://"):
        asyncio.run(tw._run_set(SETTINGS, "http://abc.ngrok.app"))


def test_set_refuses_without_secret() -> None:
    settings = Settings(
        _env_file=None, telegram_bot_token=FAKE_TOKEN, telegram_webhook_secret=""
    )
    with pytest.raises(SystemExit, match=r"api/\.env"):
        asyncio.run(tw._run_set(settings, "https://abc.ngrok.app"))


def test_set_refuses_without_token() -> None:
    settings = Settings(_env_file=None, telegram_webhook_secret=FAKE_SECRET)
    with pytest.raises(SystemExit, match=r"api/\.env"):
        asyncio.run(tw._run_set(settings, "https://abc.ngrok.app"))


def test_set_passes_secret_and_allowed_updates(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_set_with_fake_bot(
        monkeypatch, settings=SETTINGS, url="https://abc123.ngrok.app/"
    )

    assert len(_FakeBot.instances) == 1
    bot = _FakeBot.instances[0]
    assert bot.token == FAKE_TOKEN
    assert bot.calls == [
        (
            f"https://abc123.ngrok.app{tw.WEBHOOK_PATH}",
            {"secret_token": FAKE_SECRET, "allowed_updates": ["message", "callback_query"]},
        )
    ]
    assert bot.session.closed  # session always closed
    assert out == "Webhook set for abc123.ngrok.app"
    assert FAKE_SECRET not in out and FAKE_TOKEN not in out
