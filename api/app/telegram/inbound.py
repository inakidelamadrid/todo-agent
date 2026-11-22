"""Inbound anti-corruption layer (BE-006).

The only module that knows aiogram's ``Update`` shape: it maps Telegram's
hundreds of optional fields into the twelve plain fields the app actually
uses. Nothing downstream imports ``aiogram.types`` — routes, allowlist and
handlers all work with the frozen ``InboundUpdate``.
"""

from enum import StrEnum
from typing import Any, Mapping

from aiogram.types import Update
from pydantic import BaseModel, ConfigDict


class UpdateKind(StrEnum):
    TEXT = "text"
    COMMAND = "command"
    VOICE = "voice"
    PHOTO = "photo"
    DOCUMENT = "document"
    CALLBACK = "callback"
    UNSUPPORTED = "unsupported"


class InboundUpdate(BaseModel):
    """Exactly the fields the app uses, frozen. ``None`` means absent in the
    original payload."""

    model_config = ConfigDict(frozen=True)

    update_id: int
    kind: UpdateKind
    user_id: int | None = None  # who sent it
    chat_id: int | None = None
    message_id: int | None = None
    text: str | None = None  # the full message text (TEXT and COMMAND)
    command: str | None = None  # "help" for "/help" or "/help@my_bot", lower-case
    command_args: str = ""  # the rest of the line, trimmed
    caption: str | None = None  # PHOTO and DOCUMENT
    file_id: str | None = None  # VOICE, PHOTO (largest size), DOCUMENT
    file_size: int | None = None
    mime_type: str | None = None  # photos are reported as "image/jpeg"
    callback_id: str | None = None  # CALLBACK: to answer the callback query
    callback_data: str | None = None  # CALLBACK: the signed action (BE-023)


def _parse_command(text: str) -> tuple[str, str]:
    """``/Help@my_bot now`` → ``("help", "now")``."""
    head, _, rest = text.partition(" ")
    command = head[1:].split("@", 1)[0].lower()
    return command, rest.strip()


def to_inbound(update: Update) -> InboundUpdate:
    """Map one aiogram ``Update`` to an ``InboundUpdate``. Pure: no I/O.

    One branch per kind, in this order: callback, command, text, voice,
    photo, document; anything else is UNSUPPORTED with whatever IDs exist.
    """
    callback = update.callback_query
    if callback is not None:
        message = callback.message
        return InboundUpdate(
            update_id=update.update_id,
            kind=UpdateKind.CALLBACK,
            user_id=callback.from_user.id if callback.from_user else None,
            chat_id=message.chat.id if message else None,
            message_id=message.message_id if message else None,
            callback_id=callback.id,
            callback_data=callback.data,
        )

    message = update.message
    if message is None:
        # edited messages, channel posts, …: only whatever IDs exist
        edited = update.edited_message
        return InboundUpdate(
            update_id=update.update_id,
            kind=UpdateKind.UNSUPPORTED,
            user_id=edited.from_user.id if edited and edited.from_user else None,
            chat_id=edited.chat.id if edited else None,
            message_id=edited.message_id if edited else None,
        )

    ids: dict[str, Any] = {
        "update_id": update.update_id,
        "user_id": message.from_user.id if message.from_user else None,
        "chat_id": message.chat.id,
        "message_id": message.message_id,
    }

    if message.text:
        if message.text.startswith("/"):
            command, args = _parse_command(message.text)
            return InboundUpdate(
                **ids,
                kind=UpdateKind.COMMAND,
                text=message.text,
                command=command,
                command_args=args,
            )
        return InboundUpdate(**ids, kind=UpdateKind.TEXT, text=message.text)

    if message.voice:
        voice = message.voice
        return InboundUpdate(
            **ids,
            kind=UpdateKind.VOICE,
            file_id=voice.file_id,
            file_size=voice.file_size,
            mime_type=voice.mime_type,
        )

    if message.photo:
        largest = message.photo[-1]  # Telegram sends sizes ascending
        return InboundUpdate(
            **ids,
            kind=UpdateKind.PHOTO,
            caption=message.caption,
            file_id=largest.file_id,
            file_size=largest.file_size,
            mime_type="image/jpeg",
        )

    if message.document:
        document = message.document
        return InboundUpdate(
            **ids,
            kind=UpdateKind.DOCUMENT,
            caption=message.caption,
            file_id=document.file_id,
            file_size=document.file_size,
            mime_type=document.mime_type,
        )

    # stickers, locations, service messages, …
    return InboundUpdate(**ids, kind=UpdateKind.UNSUPPORTED)


def parse_inbound(payload: Mapping[str, Any]) -> InboundUpdate:
    """Validate a webhook payload as Telegram's ``Update`` and map it.

    The single entry point for callers: validation errors raise pydantic's
    ``ValidationError``; nobody else touches aiogram types.
    """
    return to_inbound(Update.model_validate(payload))


def source_ref(update: InboundUpdate) -> str | None:
    """``telegram:<chat_id>:<message_id>`` — downstream records use it to
    trace their origin (epic §5.2). ``None`` when either id is missing."""
    if update.chat_id is None or update.message_id is None:
        return None
    return f"telegram:{update.chat_id}:{update.message_id}"
