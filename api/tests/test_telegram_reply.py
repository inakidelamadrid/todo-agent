"""The bot replies: render + send from the webhook (BE-021)."""

import asyncio
import dataclasses
import logging

import pytest
from fastapi.testclient import TestClient

from app.telegram.aiogram_sender import get_sender
from app.telegram.handlers import HANDLERS, HandlerContext, Reply
from app.telegram.inbound import InboundUpdate
from app.telegram.routing import Route
from app.telegram.security import TELEGRAM_SECRET_HEADER
from app.telegram.sender import OutgoingMessage, SendFailed, SentMessage, TelegramSender
from app.telegram.service import reply
from tests.conftest import TELEGRAM_TEST_OWNER_ID, TELEGRAM_TEST_SECRET
from tests.fakes import recording_sender
from tests.telegram_fixtures import load_payload
from tests.test_telegram_handlers import _row

WEBHOOK = "/integrations/telegram/webhook"
HEADERS = {TELEGRAM_SECRET_HEADER: TELEGRAM_TEST_SECRET}

Recorded = tuple[TelegramSender, list[tuple[str, tuple]]]


def _sent_texts(calls: list[tuple[str, tuple]]) -> list[tuple[int, str]]:
    return [(args[0].chat_id, args[0].text) for op, args in calls if op == "send"]


def test_reply_renders_and_sends() -> None:
    sender, calls = recording_sender()
    sent = asyncio.run(reply(sender, 7, Reply(template="unknown_command", data={"command": "<x>"})))
    assert sent.message_id == 1
    assert calls == [
        ("send", (OutgoingMessage(chat_id=7, text="I don't know <code>/&lt;x&gt;</code>. Try /help."),)),
    ]


def test_help_command_sends_help_text_to_the_same_chat(
    telegram_webhook_client: TestClient, recorded_sends: Recorded
) -> None:
    response = telegram_webhook_client.post(WEBHOOK, json=load_payload("command"), headers=HEADERS)

    assert response.status_code == 200
    [(chat_id, text)] = _sent_texts(recorded_sends[1])
    assert chat_id == TELEGRAM_TEST_OWNER_ID
    assert text.startswith("<b>What I can do</b>")
    assert "/now:" in text


def test_unknown_command_reply_names_the_command(
    telegram_webhook_client: TestClient, recorded_sends: Recorded
) -> None:
    payload = load_payload("command")
    payload["message"]["text"] = "/frobnicate"
    payload["message"]["entities"][0]["length"] = 11

    telegram_webhook_client.post(WEBHOOK, json=payload, headers=HEADERS)

    [(_, text)] = _sent_texts(recorded_sends[1])
    assert text == "I don't know <code>/frobnicate</code>. Try /help."


def test_no_reply_sends_nothing(
    telegram_webhook_client: TestClient,
    recorded_sends: Recorded,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def silent(update: InboundUpdate, route: Route, ctx: HandlerContext) -> None:
        return None

    monkeypatch.setitem(HANDLERS, "core.help", silent)
    response = telegram_webhook_client.post(WEBHOOK, json=load_payload("command"), headers=HEADERS)

    assert response.status_code == 200
    assert recorded_sends[1] == []


def test_send_failure_marks_update_failed_and_returns_200(
    telegram_webhook_client: TestClient,
    recorded_sends: Recorded,
    migrated_test_db: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def refuse(message: OutgoingMessage) -> SentMessage:
        raise SendFailed("TelegramBadRequest")

    failing = dataclasses.replace(recorded_sends[0], send=refuse)
    telegram_webhook_client.app.dependency_overrides[get_sender] = lambda: failing  # type: ignore[attr-defined]

    with caplog.at_level(logging.WARNING):
        response = telegram_webhook_client.post(WEBHOOK, json=load_payload("command"), headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    row = _row(migrated_test_db, 700000002)
    assert row is not None and row.status == "failed"
    assert "telegram.reply_failed SendFailed" in caplog.text
    assert "What I can do" not in caplog.text


def test_stranger_gets_no_reply(
    telegram_webhook_client: TestClient, recorded_sends: Recorded
) -> None:
    response = telegram_webhook_client.post(
        WEBHOOK, json=load_payload("stranger_text"), headers=HEADERS
    )
    assert response.status_code == 200
    assert recorded_sends[1] == []


def test_duplicate_update_gets_one_reply(
    telegram_webhook_client: TestClient, recorded_sends: Recorded
) -> None:
    payload = load_payload("command")
    for _ in range(2):
        assert telegram_webhook_client.post(WEBHOOK, json=payload, headers=HEADERS).status_code == 200
    assert len(_sent_texts(recorded_sends[1])) == 1
