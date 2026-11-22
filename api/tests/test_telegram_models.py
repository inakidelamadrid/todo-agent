"""Tests for the telegram_updates table (BE-010).

Shape is inspected from SQLAlchemy metadata; PK and CHECK enforcement are
proven against the per-worker migrated database.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.telegram.models import TelegramUpdate

T = TypeVar("T")

EXPECTED_COLUMNS = {
    "update_id",
    "chat_id",
    "message_id",
    "kind",
    "route",
    "status",
    "received_at",
}


def _run(database: str, scenario: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async def _with_session() -> T:
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=database).database_url
        )
        try:
            async with AsyncSession(engine) as session:
                return await scenario(session)
        finally:
            await engine.dispose()

    return asyncio.run(_with_session())


def test_telegram_updates_table_shape() -> None:
    table = TelegramUpdate.__table__
    assert table.name == "telegram_updates"
    assert set(table.columns.keys()) == EXPECTED_COLUMNS

    assert [c.name for c in table.primary_key.columns] == ["update_id"]
    assert not table.c.update_id.nullable
    assert table.c.chat_id.nullable
    assert table.c.message_id.nullable
    # No column could hold message content: the only strings are short enums.
    assert {c.name for c in table.columns if c.type.__class__.__name__ == "String"} == {
        "kind",
        "route",
        "status",
    }

    checks = {c.name for c in table.constraints if c.name}
    assert {"ck_telegram_updates_kind", "ck_telegram_updates_status"} <= checks
    assert "ix_telegram_updates_received_at" in {i.name for i in table.indexes}


def test_duplicate_update_id_violates_primary_key(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(TelegramUpdate(update_id=700000001, kind="text"))
        await session.flush()
        session.add(TelegramUpdate(update_id=700000001, kind="text"))
        with pytest.raises(IntegrityError):
            await session.flush()

    _run(migrated_test_db, scenario)


def test_status_check_rejects_unknown_value(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(TelegramUpdate(update_id=700000002, kind="text", status="lost"))
        with pytest.raises(IntegrityError):
            await session.flush()

    _run(migrated_test_db, scenario)
