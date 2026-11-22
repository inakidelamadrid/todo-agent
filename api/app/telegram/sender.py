"""Outbound sender port (BE-018).

The one agreed shape for "send, edit, delete a Telegram message". Every
outbound feature calls this port, never aiogram: BE-019 supplies the real
adapter, tests use ``tests.fakes.recording_sender``. Nothing here imports
aiogram, and the errors are plain types so callers never import aiogram's.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator

CALLBACK_DATA_MAX_BYTES = 64  # Telegram's limit, in bytes
MESSAGE_TEXT_MAX_CHARS = 4096


class Button(BaseModel):
    """One inline button. ``callback_data`` is limited in bytes, not chars."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=40)
    callback_data: str = Field(min_length=1)

    @field_validator("callback_data")
    @classmethod
    def _fits_in_64_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > CALLBACK_DATA_MAX_BYTES:
            raise ValueError(f"callback_data must be at most {CALLBACK_DATA_MAX_BYTES} bytes")
        return value


class OutgoingMessage(BaseModel):
    """A message ready to send: ``text`` is already rendered, escaped HTML."""

    model_config = ConfigDict(frozen=True)

    chat_id: int
    text: str = Field(min_length=1, max_length=MESSAGE_TEXT_MAX_CHARS)
    buttons: tuple[tuple[Button, ...], ...] = ()  # rows of buttons


class SentMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: int


@dataclass(frozen=True)
class TelegramSender:
    send: Callable[[OutgoingMessage], Awaitable[SentMessage]]
    edit: Callable[[int, int, str], Awaitable[None]]  # chat_id, message_id, new text
    delete: Callable[[int, int], Awaitable[None]]  # chat_id, message_id
    answer_callback: Callable[[str, str], Awaitable[None]]  # callback_id, notice ("" for none)


class SendFailed(Exception):
    """Telegram refused or could not be reached."""


class RateLimited(SendFailed):
    def __init__(self, retry_after: float) -> None:
        super().__init__(f"rate limited, retry after {retry_after}s")
        self.retry_after = retry_after


class TelegramNotConfigured(SendFailed):
    """No bot token: the app runs, but nothing can be sent."""
