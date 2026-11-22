"""Tests for the handler registry and webhook dispatch (BE-015)."""

import asyncio
import logging
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.telegram.handlers import HANDLERS, HandlerContext, Reply, resolve
from app.telegram.inbound import InboundUpdate, UpdateKind
from app.telegram.models import TelegramUpdate
from app.telegram.routing import Route
from app.telegram.security import TELEGRAM_SECRET_HEADER
from tests.conftest import TELEGRAM_TEST_SECRET
from tests.telegram_fixtures import load_payload

WEBHOOK = "/integrations/telegram/webhook"
SECRET = TELEGRAM_TEST_SECRET


@pytest.fixture(name="webhook_client")
def _webhook_client(telegram_webhook_client: TestClient) -> TestClient:
    return telegram_webhook_client


def _row(worker_db: str, update_id: int) -> TelegramUpdate | None:
    async def read() -> TelegramUpdate | None:
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=worker_db).database_url
        )
        try:
            async with AsyncSession(engine) as session:
                return await session.get(TelegramUpdate, update_id)
        finally:
            await engine.dispose()

    return asyncio.run(read())


def _ctx() -> HandlerContext:
    # Core handlers never touch the session; a Mock keeps the port honest.
    from unittest.mock import Mock

    return HandlerContext(session=Mock(), now=datetime.now(timezone.utc))


_UPDATE = InboundUpdate(update_id=1, kind=UpdateKind.COMMAND, command="help")
_ROUTE = Route(kind="command", target="core.help")


def test_resolve_returns_registered_handler() -> None:
    assert resolve("core.help") is HANDLERS["core.help"]


def test_resolve_falls_back_to_not_available() -> None:
    reply = asyncio.run(resolve("tasks.now")(_UPDATE, _ROUTE, _ctx()))
    assert reply == Reply(template="not_available")


def test_help_handler_replies_with_help_template() -> None:
    reply = asyncio.run(HANDLERS["core.help"](_UPDATE, _ROUTE, _ctx()))
    assert reply == Reply(template="help")


def test_webhook_records_route_target(
    webhook_client: TestClient, migrated_test_db: str
) -> None:
    response = webhook_client.post(
        WEBHOOK,
        json=load_payload("command"),
        headers={TELEGRAM_SECRET_HEADER: SECRET},
    )
    assert response.status_code == 200
    row = _row(migrated_test_db, 700000002)
    assert row is not None
    assert row.route == "core.help"
    assert row.status == "processed"


def test_failing_handler_marks_failed_and_returns_200(
    webhook_client: TestClient,
    migrated_test_db: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def blow_up(update: InboundUpdate, route: Route, ctx: HandlerContext) -> Reply:
        raise RuntimeError("boom")

    monkeypatch.setitem(HANDLERS, "core.help", blow_up)
    with caplog.at_level(logging.ERROR):
        response = webhook_client.post(
            WEBHOOK,
            json=load_payload("command"),
            headers={TELEGRAM_SECRET_HEADER: SECRET},
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    row = _row(migrated_test_db, 700000002)
    assert row is not None
    assert row.status == "failed"
    assert row.route == "core.help"

    assert "telegram.handler_failed" in caplog.text
    # The log carries no update content.
    assert "/help" not in caplog.text


def test_unregistered_command_is_acknowledged_and_recorded(
    webhook_client: TestClient, migrated_test_db: str
) -> None:
    payload = load_payload("command")
    payload["message"]["text"] = "/vault"
    payload["update_id"] = 700000111
    response = webhook_client.post(
        WEBHOOK, json=payload, headers={TELEGRAM_SECRET_HEADER: SECRET}
    )
    assert response.status_code == 200
    row = _row(migrated_test_db, 700000111)
    assert row is not None
    assert row.route == "vault.await_upload"  # placeholder handled it
    assert row.status == "processed"
