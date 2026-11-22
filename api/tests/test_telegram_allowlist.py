"""Tests for the owner allowlist (BE-009).

Predicate-level tests are pure; the route test drives stranger_text.json
through the real app and checks the counter log carries no identifiers.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.telegram.allowlist import is_allowed
from app.telegram.inbound import InboundUpdate, UpdateKind, to_inbound
from app.telegram.security import TELEGRAM_SECRET_HEADER
from tests.conftest import TELEGRAM_TEST_OWNER_ID, TELEGRAM_TEST_SECRET
from tests.telegram_fixtures import load_payload, load_update

WEBHOOK = "/integrations/telegram/webhook"
SECRET = TELEGRAM_TEST_SECRET
OWNER = TELEGRAM_TEST_OWNER_ID


def test_owner_is_allowed() -> None:
    assert is_allowed(to_inbound(load_update("text")), OWNER) is True


def test_stranger_is_not_allowed() -> None:
    assert is_allowed(to_inbound(load_update("stranger_text")), OWNER) is False


def test_owner_in_another_chat_is_not_allowed() -> None:
    update = InboundUpdate(
        update_id=1, kind=UpdateKind.TEXT, user_id=OWNER, chat_id=555555, text="hi"
    )
    assert is_allowed(update, OWNER) is False


def test_nobody_is_allowed_when_unconfigured() -> None:
    assert is_allowed(to_inbound(load_update("text")), None) is False


def test_update_without_user_is_not_allowed() -> None:
    update = InboundUpdate(update_id=1, kind=UpdateKind.UNSUPPORTED, chat_id=OWNER)
    assert is_allowed(update, OWNER) is False


@pytest.fixture(name="webhook_client")
def _webhook_client(telegram_webhook_client: TestClient) -> TestClient:
    return telegram_webhook_client


def test_webhook_drops_stranger_with_200_and_logs_counter(
    webhook_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        response = webhook_client.post(
            WEBHOOK,
            json=load_payload("stranger_text"),
            headers={TELEGRAM_SECRET_HEADER: SECRET},
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    ignored = [r for r in caplog.records if r.message == "telegram.ignored"]
    assert len(ignored) == 1
    # The counter line carries no identifiers or content.
    assert "999999" not in caplog.text
    assert "buy milk" not in caplog.text


def test_webhook_accepts_owner_without_ignored_log(
    webhook_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        response = webhook_client.post(
            WEBHOOK, json=load_payload("text"), headers={TELEGRAM_SECRET_HEADER: SECRET}
        )
    assert response.status_code == 200
    assert "telegram.ignored" not in caplog.text
