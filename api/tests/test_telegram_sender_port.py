"""Sender port value types and the recording fake (BE-018)."""

import asyncio
import dataclasses

import pytest
from pydantic import ValidationError

from app.telegram.sender import Button, OutgoingMessage, SentMessage
from tests.fakes import recording_sender


def test_outgoing_message_rejects_empty_and_overlong_text() -> None:
    with pytest.raises(ValidationError):
        OutgoingMessage(chat_id=1, text="")
    with pytest.raises(ValidationError):
        OutgoingMessage(chat_id=1, text="x" * 4097)
    assert OutgoingMessage(chat_id=1, text="x" * 4096).text == "x" * 4096


def test_button_rejects_callback_data_over_64_bytes() -> None:
    assert Button(text="ok", callback_data="a" * 64)
    with pytest.raises(ValidationError):
        Button(text="ok", callback_data="a" * 65)
    # 32 two-byte characters fit; 33 don't, though 33 chars < 64.
    assert Button(text="ok", callback_data="é" * 32)
    with pytest.raises(ValidationError):
        Button(text="ok", callback_data="é" * 33)


def test_recording_sender_records_send_edit_delete_answer() -> None:
    sender, calls = recording_sender()
    message = OutgoingMessage(chat_id=7, text="hi")

    async def _run() -> list[SentMessage]:
        first = await sender.send(message)
        second = await sender.send(message)
        await sender.edit(7, 1, "edited")
        await sender.delete(7, 2)
        await sender.answer_callback("cb-1", "")
        return [first, second]

    sent = asyncio.run(_run())

    assert [s.message_id for s in sent] == [1, 2]
    assert calls == [
        ("send", (message,)),
        ("send", (message,)),
        ("edit", (7, 1, "edited")),
        ("delete", (7, 2)),
        ("answer_callback", ("cb-1", "")),
    ]


def test_types_are_frozen() -> None:
    message = OutgoingMessage(chat_id=1, text="hi")
    with pytest.raises(ValidationError):
        message.text = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Button(text="a", callback_data="b").text = "c"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        SentMessage(message_id=1).message_id = 2  # type: ignore[misc]
    sender, _ = recording_sender()
    with pytest.raises(dataclasses.FrozenInstanceError):
        sender.send = sender.send  # type: ignore[misc]
