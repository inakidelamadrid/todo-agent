"""aiogram adapter for the sender port (BE-019). Mocked Bot, no network."""

import asyncio
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import SendMessage
from aiogram.types import InlineKeyboardMarkup
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import get_settings
from app.telegram import aiogram_sender as module
from app.telegram.aiogram_sender import aiogram_sender, open_sender, unconfigured_sender
from app.telegram.sender import (
    Button,
    OutgoingMessage,
    RateLimited,
    SendFailed,
    TelegramNotConfigured,
)

FAKE_TOKEN = "123456:SECRET-token-never-in-errors"


def _bot() -> AsyncMock:
    bot = AsyncMock(spec=Bot)
    bot.send_message.return_value = MagicMock(message_id=42)
    return bot


def test_send_passes_text_html_and_no_markup_without_buttons() -> None:
    bot = _bot()
    asyncio.run(aiogram_sender(bot).send(OutgoingMessage(chat_id=7, text="<b>hi</b>")))

    kwargs = bot.send_message.await_args.kwargs
    assert kwargs["chat_id"] == 7
    assert kwargs["text"] == "<b>hi</b>"
    assert kwargs["parse_mode"] == "HTML"
    assert kwargs["reply_markup"] is None
    assert kwargs["link_preview_options"].is_disabled is True


def test_send_builds_inline_keyboard_rows() -> None:
    bot = _bot()
    rows = (
        (Button(text="Yes", callback_data="y"), Button(text="No", callback_data="n")),
        (Button(text="Later", callback_data="l"),),
    )
    asyncio.run(aiogram_sender(bot).send(OutgoingMessage(chat_id=7, text="?", buttons=rows)))

    markup = bot.send_message.await_args.kwargs["reply_markup"]
    assert isinstance(markup, InlineKeyboardMarkup)
    assert [[(b.text, b.callback_data) for b in row] for row in markup.inline_keyboard] == [
        [("Yes", "y"), ("No", "n")],
        [("Later", "l")],
    ]


def test_send_returns_message_id() -> None:
    sent = asyncio.run(aiogram_sender(_bot()).send(OutgoingMessage(chat_id=7, text="hi")))
    assert sent.message_id == 42


def test_edit_delete_answer_call_the_bot() -> None:
    bot = _bot()
    sender = aiogram_sender(bot)

    async def _run() -> None:
        await sender.edit(7, 3, "new")
        await sender.delete(7, 3)
        await sender.answer_callback("cb-1", "")
        await sender.answer_callback("cb-2", "Saved")

    asyncio.run(_run())

    edit = bot.edit_message_text.await_args.kwargs
    assert (edit["chat_id"], edit["message_id"], edit["text"], edit["parse_mode"]) == (
        7, 3, "new", "HTML",
    )
    bot.delete_message.assert_awaited_once_with(chat_id=7, message_id=3)
    assert [c.kwargs for c in bot.answer_callback_query.await_args_list] == [
        {"callback_query_id": "cb-1", "text": None},
        {"callback_query_id": "cb-2", "text": "Saved"},
    ]


def _method() -> SendMessage:
    return SendMessage(chat_id=7, text="private message text")


def test_retry_after_maps_to_rate_limited_with_seconds() -> None:
    bot = _bot()
    bot.send_message.side_effect = TelegramRetryAfter(_method(), "Too Many Requests", 17)

    with pytest.raises(RateLimited) as caught:
        asyncio.run(aiogram_sender(bot).send(OutgoingMessage(chat_id=7, text="hi")))

    assert caught.value.retry_after == 17.0
    assert isinstance(caught.value, SendFailed)


@pytest.mark.parametrize(
    "error",
    [
        TelegramBadRequest(_method(), f"bad request for bot{FAKE_TOKEN}"),
        TelegramNetworkError(_method(), f"https://api.telegram.org/bot{FAKE_TOKEN}/sendMessage"),
    ],
)
def test_other_api_error_maps_to_send_failed(error: Exception) -> None:
    bot = _bot()
    bot.delete_message.side_effect = error

    with pytest.raises(SendFailed) as caught:
        asyncio.run(aiogram_sender(bot).delete(7, 3))

    assert str(caught.value) == type(error).__name__
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
    assert FAKE_TOKEN not in repr(caught.value)


@pytest.mark.parametrize("operation", ["send", "edit", "delete", "answer_callback"])
def test_unconfigured_sender_raises_not_configured(operation: str) -> None:
    args = {
        "send": (OutgoingMessage(chat_id=7, text="hi"),),
        "edit": (7, 3, "x"),
        "delete": (7, 3),
        "answer_callback": ("cb", ""),
    }[operation]
    with pytest.raises(TelegramNotConfigured):
        asyncio.run(getattr(unconfigured_sender(), operation)(*args))


def test_open_sender_closes_bot_session(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.session.close = AsyncMock()
    monkeypatch.setattr(module, "Bot", MagicMock(return_value=bot))

    async def _run() -> None:
        async with open_sender(FAKE_TOKEN):
            bot.session.close.assert_not_awaited()

    asyncio.run(_run())
    module.Bot.assert_called_once_with(token=FAKE_TOKEN)
    bot.session.close.assert_awaited_once()


@pytest.fixture()
def no_token(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")  # overrides any api/.env value
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_app_starts_without_token(no_token: None) -> None:
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        with pytest.raises(TelegramNotConfigured):
            asyncio.run(app.state.telegram_sender.delete(7, 3))
