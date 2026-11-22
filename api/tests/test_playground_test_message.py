"""Playground: send a test message to the owner's chat now (BE-079)."""

import asyncio
import dataclasses
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings, get_settings
from app.telegram.aiogram_sender import get_sender, unconfigured_sender
from app.telegram.playground.limits import may_send
from app.telegram.playground.models import PlaygroundAction
from app.telegram.sender import OutgoingMessage, RateLimited, SentMessage, TelegramSender
from tests.conftest import KEY_ONE, TELEGRAM_TEST_OWNER_ID, sign_token
from tests.fakes import recording_sender
from tests.test_playground_templates import (  # noqa: F401 (fixture)
    ADMIN,
    OTHER_USER_ID,
    _client,
    bearer,
    clean_actions,
)

URL = "/admin/telegram/test-message"
BODY = {"template": "help", "data": {}}

Recorded = tuple[TelegramSender, list[tuple[str, tuple]]]


@pytest.fixture()
def recorded() -> Recorded:
    return recording_sender()


def _with_sender(client: TestClient, sender: TelegramSender) -> TestClient:
    client.app.dependency_overrides[get_sender] = lambda: sender  # type: ignore[attr-defined]
    return client


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch,
    migrated_test_db: str,
    clean_actions: None,
    recorded: Recorded,
) -> Iterator[TestClient]:
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_ID", str(TELEGRAM_TEST_OWNER_ID))
    for c in _client(monkeypatch, migrated_test_db, playground=True):
        yield _with_sender(c, recorded[0])


@pytest.fixture()
def off_client(
    monkeypatch: pytest.MonkeyPatch, migrated_test_db: str, clean_actions: None
) -> Iterator[TestClient]:
    yield from _client(monkeypatch, migrated_test_db, playground=False)


def _outcomes(db: str) -> list[str]:
    async def read() -> list[str]:
        engine = create_async_engine(Settings(api_keys="test-suite", postgres_db=db).database_url)
        try:
            async with AsyncSession(engine) as session:
                rows = await session.scalars(
                    select(PlaygroundAction.outcome)
                    .where(PlaygroundAction.tool == "test_message")
                    .order_by(PlaygroundAction.created_at)
                )
                return list(rows)
        finally:
            await engine.dispose()

    return asyncio.run(read())


def _sends(recorded: Recorded) -> list[OutgoingMessage]:
    return [args[0] for op, args in recorded[1] if op == "send"]


# --- Guards -----------------------------------------------------------------


def test_test_message_without_credentials_returns_401(client: TestClient) -> None:
    assert client.post(URL, json=BODY).status_code == 401


def test_test_message_as_non_admin_returns_403(client: TestClient) -> None:
    headers = bearer(sign_token(sub=OTHER_USER_ID))
    assert client.post(URL, json=BODY, headers=headers).status_code == 403


def test_test_message_as_machine_returns_403(client: TestClient) -> None:
    assert client.post(URL, json=BODY, headers={"X-API-Key": KEY_ONE}).status_code == 403


def test_test_message_when_playground_off_returns_404(off_client: TestClient) -> None:
    assert off_client.post(URL, json=BODY, headers=ADMIN).status_code == 404


# --- Behaviour --------------------------------------------------------------


def test_may_send_boundary() -> None:
    assert may_send(9) is True
    assert may_send(10) is False


def test_test_message_sends_to_allowed_chat_only(
    client: TestClient, recorded: Recorded, migrated_test_db: str
) -> None:
    response = client.post(URL, json=BODY, headers=ADMIN)

    assert response.status_code == 200
    assert response.json() == {"messageId": 1}
    [message] = _sends(recorded)
    assert message.chat_id == TELEGRAM_TEST_OWNER_ID
    assert message.text.startswith("<b>What I can do</b>")
    assert _outcomes(migrated_test_db) == ["ok"]


def test_eleventh_in_an_hour_is_429_and_recorded_rejected(
    client: TestClient, recorded: Recorded, migrated_test_db: str
) -> None:
    for _ in range(10):
        assert client.post(URL, json=BODY, headers=ADMIN).status_code == 200

    response = client.post(URL, json=BODY, headers=ADMIN)

    assert response.status_code == 429
    assert response.json() == {"detail": "Test message limit reached (10 per hour)"}
    assert len(_sends(recorded)) == 10
    assert _outcomes(migrated_test_db) == ["ok"] * 10 + ["rejected"]


def test_unconfigured_telegram_is_409(client: TestClient, migrated_test_db: str) -> None:
    _with_sender(client, unconfigured_sender())
    response = client.post(URL, json=BODY, headers=ADMIN)
    assert response.status_code == 409
    assert response.json() == {"detail": "TELEGRAM_BOT_TOKEN is not set"}

    no_chat = get_settings().model_copy(update={"telegram_allowed_user_id": None})
    client.app.dependency_overrides[get_settings] = lambda: no_chat  # type: ignore[attr-defined]
    response = client.post(URL, json=BODY, headers=ADMIN)
    assert response.status_code == 409
    assert response.json() == {"detail": "TELEGRAM_ALLOWED_USER_ID is not set"}

    assert _outcomes(migrated_test_db) == ["failed", "failed"]


def test_telegram_refusal_is_502_and_recorded_failed(
    client: TestClient, recorded: Recorded, migrated_test_db: str
) -> None:
    async def refuse(message: OutgoingMessage) -> SentMessage:
        raise RateLimited(retry_after=5)

    _with_sender(client, dataclasses.replace(recorded[0], send=refuse))
    response = client.post(URL, json=BODY, headers=ADMIN)

    assert response.status_code == 502
    assert response.json() == {"detail": "Telegram refused the message (RateLimited)"}
    assert _outcomes(migrated_test_db) == ["failed"]


def test_unknown_template_is_404_and_sends_nothing(
    client: TestClient, recorded: Recorded, migrated_test_db: str
) -> None:
    response = client.post(URL, json={"template": "nope"}, headers=ADMIN)
    assert response.status_code == 404
    assert _sends(recorded) == []
    assert _outcomes(migrated_test_db) == ["rejected"]


def test_request_cannot_set_recipient(client: TestClient, recorded: Recorded) -> None:
    response = client.post(URL, json={**BODY, "chatId": 999999}, headers=ADMIN)
    assert response.status_code == 422
    assert _sends(recorded) == []
