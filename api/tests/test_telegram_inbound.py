"""Tests for the inbound anti-corruption layer (BE-006).

One test per to_inbound branch, driven by the BE-005 recorded payloads.
"""

import pytest
from aiogram.types import Update
from pydantic import ValidationError

from app.telegram.inbound import InboundUpdate, UpdateKind, source_ref, to_inbound
from tests.telegram_fixtures import load_payload, load_update


def test_text_message_maps_to_text() -> None:
    inbound = to_inbound(load_update("text"))
    assert inbound.kind is UpdateKind.TEXT
    assert inbound.update_id == 700000001
    assert inbound.user_id == 111111
    assert inbound.chat_id == 111111
    assert inbound.message_id == 101
    assert inbound.text == "buy milk tomorrow"
    assert inbound.command is None
    assert inbound.file_id is None


def test_command_strips_slash_and_bot_suffix() -> None:
    payload = load_payload("command")
    payload["message"]["text"] = "/Help@my_bot now"
    inbound = to_inbound(Update.model_validate(payload))
    assert inbound.kind is UpdateKind.COMMAND
    assert inbound.command == "help"
    assert inbound.command_args == "now"
    assert inbound.text == "/Help@my_bot now"


def test_command_fixture_maps_to_help_command() -> None:
    inbound = to_inbound(load_update("command"))
    assert inbound.kind is UpdateKind.COMMAND
    assert inbound.command == "help"
    assert inbound.command_args == ""
    assert inbound.text == "/help"


def test_voice_carries_file_id_size_and_mime() -> None:
    inbound = to_inbound(load_update("voice"))
    assert inbound.kind is UpdateKind.VOICE
    assert inbound.file_id == "synthetic_voice_file_id"
    assert inbound.file_size == 10240
    assert inbound.mime_type == "audio/ogg"
    assert inbound.text is None


def test_photo_uses_largest_size_and_keeps_caption() -> None:
    inbound = to_inbound(load_update("photo"))
    assert inbound.kind is UpdateKind.PHOTO
    assert inbound.file_id == "synthetic_photo_l"  # the last, largest size
    assert inbound.file_size == 90000
    assert inbound.mime_type == "image/jpeg"
    assert inbound.caption == "vault passport"


def test_document_carries_mime_type() -> None:
    inbound = to_inbound(load_update("document"))
    assert inbound.kind is UpdateKind.DOCUMENT
    assert inbound.file_id == "synthetic_document_file_id"
    assert inbound.file_size == 51200
    assert inbound.mime_type == "application/pdf"


def test_callback_carries_id_data_and_origin_message() -> None:
    inbound = to_inbound(load_update("callback_query"))
    assert inbound.kind is UpdateKind.CALLBACK
    assert inbound.callback_id == "synthetic_callback_query_id"
    assert inbound.callback_data == "placeholder"
    assert inbound.user_id == 111111
    assert inbound.chat_id == 111111
    assert inbound.message_id == 106


def test_unknown_update_is_unsupported() -> None:
    payload = {
        "update_id": 700000099,
        "edited_message": {
            "message_id": 108,
            "date": 1763000007,
            "from": {"id": 111111, "is_bot": False, "first_name": "Owner"},
            "chat": {"id": 111111, "type": "private", "first_name": "Owner"},
            "text": "buy milk today",
            "edit_date": 1763000008,
        },
    }
    inbound = to_inbound(Update.model_validate(payload))
    assert inbound.kind is UpdateKind.UNSUPPORTED
    assert inbound.update_id == 700000099
    assert inbound.chat_id == 111111
    assert inbound.message_id == 108
    assert inbound.text is None


def test_stranger_text_maps_normally() -> None:
    # Mapping does not filter; the allowlist (BE-009) decides.
    inbound = to_inbound(load_update("stranger_text"))
    assert inbound.kind is UpdateKind.TEXT
    assert inbound.user_id == 999999


def test_source_ref_format() -> None:
    inbound = to_inbound(load_update("text"))
    assert source_ref(inbound) == "telegram:111111:101"


def test_source_ref_is_none_without_message() -> None:
    update = InboundUpdate(update_id=1, kind=UpdateKind.UNSUPPORTED)
    assert source_ref(update) is None


def test_inbound_update_is_frozen() -> None:
    inbound = to_inbound(load_update("text"))
    with pytest.raises(ValidationError):
        inbound.text = "mutated"  # type: ignore[misc]
