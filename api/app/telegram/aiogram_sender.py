"""aiogram adapter for the sender port (BE-019).

The only module that performs Telegram HTTP calls, and the only one under
``app/`` that imports ``aiogram.Bot``. Each operation is a one-to-one
translation to a Bot API method; aiogram's errors are mapped to the port's
plain ones in ``_mapped_errors``, which never echoes the request (it holds
the token in its URL and the message text).
"""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from aiogram import Bot
from aiogram.exceptions import AiogramError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from fastapi import Request

from app.telegram.sender import (
    Button,
    OutgoingMessage,
    RateLimited,
    SendFailed,
    SentMessage,
    TelegramNotConfigured,
    TelegramSender,
)

_NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


@contextmanager
def _mapped_errors() -> Iterator[None]:
    """aiogram errors → port errors. The message is the type name only."""
    try:
        yield
    except TelegramRetryAfter as error:
        raise RateLimited(retry_after=float(error.retry_after)) from None
    except AiogramError as error:  # API errors and network errors alike
        raise SendFailed(type(error).__name__) from None


def _keyboard(rows: tuple[tuple[Button, ...], ...]) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b.text, callback_data=b.callback_data) for b in row]
            for row in rows
        ]
    )


def aiogram_sender(bot: Bot) -> TelegramSender:
    async def send(message: OutgoingMessage) -> SentMessage:
        with _mapped_errors():
            sent = await bot.send_message(
                chat_id=message.chat_id,
                text=message.text,
                parse_mode="HTML",
                link_preview_options=_NO_PREVIEW,
                reply_markup=_keyboard(message.buttons),
            )
        return SentMessage(message_id=sent.message_id)

    async def edit(chat_id: int, message_id: int, text: str) -> None:
        with _mapped_errors():
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML",
                link_preview_options=_NO_PREVIEW,
            )

    async def delete(chat_id: int, message_id: int) -> None:
        with _mapped_errors():
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

    async def answer_callback(callback_id: str, text: str) -> None:
        with _mapped_errors():
            await bot.answer_callback_query(callback_query_id=callback_id, text=text or None)

    return TelegramSender(send=send, edit=edit, delete=delete, answer_callback=answer_callback)


def unconfigured_sender() -> TelegramSender:
    """Every operation raises ``TelegramNotConfigured``; the app still starts."""

    async def _refuse(*_args: object) -> None:
        raise TelegramNotConfigured("TELEGRAM_BOT_TOKEN is not set")

    return TelegramSender(send=_refuse, edit=_refuse, delete=_refuse, answer_callback=_refuse)  # type: ignore[arg-type]


@asynccontextmanager
async def open_sender(token: str) -> AsyncIterator[TelegramSender]:
    """The app's sender for its lifetime: one ``Bot`` when a token is set,
    its HTTP session closed on exit; ``unconfigured_sender`` otherwise."""
    if not token:
        yield unconfigured_sender()
        return
    bot = Bot(token=token)
    try:
        yield aiogram_sender(bot)
    finally:
        await bot.session.close()


def get_sender(request: Request) -> TelegramSender:
    return request.app.state.telegram_sender
