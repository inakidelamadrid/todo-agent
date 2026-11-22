"""Tests for POST /integrations/telegram/webhook (BE-008, BE-009, BE-012).

The route is public: no API key, guarded by the Telegram secret header.
Every recorded fixture is acknowledged; the owner's updates are claimed
exactly once (duplicate deliveries return 200 and do nothing) and marked
``processed`` — strangers never reach the database.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.telegram.models import TelegramUpdate
from app.telegram.security import TELEGRAM_SECRET_HEADER
from tests.conftest import KEY_ONE, TELEGRAM_TEST_SECRET
from tests.telegram_fixtures import FIXTURE_NAMES, load_payload

WEBHOOK = "/integrations/telegram/webhook"
SECRET = TELEGRAM_TEST_SECRET


@pytest.fixture(name="webhook_client")
def _webhook_client(telegram_webhook_client: TestClient) -> TestClient:
    return telegram_webhook_client


def _update_rows(worker_db: str) -> list[TelegramUpdate]:
    async def read() -> list[TelegramUpdate]:
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=worker_db).database_url
        )
        try:
            async with AsyncSession(engine) as session:
                result = await session.scalars(select(TelegramUpdate))
                return list(result.all())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def _secret() -> dict[str, str]:
    return {TELEGRAM_SECRET_HEADER: SECRET}


# --- guard (BE-008) ----------------------------------------------------------


def test_webhook_without_secret_is_401(webhook_client: TestClient) -> None:
    assert webhook_client.post(WEBHOOK, json={}).status_code == 401


def test_webhook_with_wrong_secret_is_401(webhook_client: TestClient) -> None:
    response = webhook_client.post(
        WEBHOOK, json={}, headers={TELEGRAM_SECRET_HEADER: "wrong-secret_0123456789"}
    )
    assert response.status_code == 401


def test_webhook_with_api_key_but_no_secret_is_401(webhook_client: TestClient) -> None:
    # A valid API key alone does not open the webhook.
    response = webhook_client.post(WEBHOOK, json={}, headers={"X-API-Key": KEY_ONE})
    assert response.status_code == 401


# --- parse + ack (BE-008/BE-009) ---------------------------------------------


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_webhook_accepts_each_fixture(webhook_client: TestClient, name: str) -> None:
    response = webhook_client.post(WEBHOOK, json=load_payload(name), headers=_secret())
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_unparseable_update_is_still_200(webhook_client: TestClient) -> None:
    response = webhook_client.post(WEBHOOK, json={"foo": 1}, headers=_secret())
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_webhook_is_not_in_openapi(webhook_client: TestClient) -> None:
    response = webhook_client.get("/openapi.json")
    assert response.status_code == 200
    assert WEBHOOK not in response.text


# --- exactly once (BE-012) ----------------------------------------------------


def test_same_update_twice_stores_one_row(
    webhook_client: TestClient, migrated_test_db: str
) -> None:
    for _ in range(2):
        webhook_client.post(WEBHOOK, json=load_payload("text"), headers=_secret())
    rows = _update_rows(migrated_test_db)
    assert [r.update_id for r in rows] == [700000001]


def test_second_delivery_returns_200(webhook_client: TestClient) -> None:
    first = webhook_client.post(WEBHOOK, json=load_payload("text"), headers=_secret())
    second = webhook_client.post(WEBHOOK, json=load_payload("text"), headers=_secret())
    assert first.status_code == 200
    assert second.status_code == 200


def test_stranger_update_is_not_stored(
    webhook_client: TestClient, migrated_test_db: str
) -> None:
    response = webhook_client.post(
        WEBHOOK, json=load_payload("stranger_text"), headers=_secret()
    )
    assert response.status_code == 200
    assert _update_rows(migrated_test_db) == []


def test_new_update_is_marked_processed(
    webhook_client: TestClient, migrated_test_db: str
) -> None:
    webhook_client.post(WEBHOOK, json=load_payload("text"), headers=_secret())
    (row,) = _update_rows(migrated_test_db)
    assert row.status == "processed"
