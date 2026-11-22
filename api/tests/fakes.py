"""Test fakes for the app's ports.

Session token (BE-060): no test ever needs a real key: the fake decoder maps
token strings to claim dicts, and unknown tokens decode to ``None`` (not
validly signed).

Telegram sender (BE-018): ``recording_sender`` records every call and never
touches the network.
"""

from itertools import count
from typing import Any

from app.session_token import Claims, DecodeToken
from app.telegram.sender import OutgoingMessage, SentMessage, TelegramSender


def make_claims(**overrides: Any) -> dict[str, Any]:
    """A valid claim set; tests tweak it with overrides."""
    return {
        "sub": "user_owner",
        "azp": "http://localhost:5173",
        "exp": 4_000_000_000,  # far in the future, no clock needed
        **overrides,
    }


def fake_decoder(table: "dict[str, Claims]") -> DecodeToken:
    """Return claims for tokens in ``table``; ``None`` for anything else."""

    def decode(token: str) -> "Claims | None":
        return table.get(token)

    return decode


def recording_sender() -> "tuple[TelegramSender, list[tuple[str, tuple]]]":
    """A sender that appends ``(operation, args)`` to the returned list.

    ``send`` returns increasing message IDs from 1.
    """
    calls: list[tuple[str, tuple]] = []
    message_ids = count(1)

    async def send(message: OutgoingMessage) -> SentMessage:
        calls.append(("send", (message,)))
        return SentMessage(message_id=next(message_ids))

    async def edit(chat_id: int, message_id: int, text: str) -> None:
        calls.append(("edit", (chat_id, message_id, text)))

    async def delete(chat_id: int, message_id: int) -> None:
        calls.append(("delete", (chat_id, message_id)))

    async def answer_callback(callback_id: str, text: str) -> None:
        calls.append(("answer_callback", (callback_id, text)))

    return TelegramSender(send=send, edit=edit, delete=delete, answer_callback=answer_callback), calls
