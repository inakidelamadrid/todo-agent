"""Integration tests for the telegram update repository (BE-011).

Claiming is one atomic statement; the concurrency test gathers two sessions
claiming the same update_id and requires exactly one True — a
select-then-insert implementation could not satisfy it.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.telegram.inbound import to_inbound
from app.telegram.models import TelegramUpdate
from app.telegram.repository import claim_update, delete_updates_before, mark_update
from tests.telegram_fixtures import load_update

OWNER_TEXT = to_inbound(load_update("text"))
SECOND_ID = 700000050


def _engine(database: str):
    return create_async_engine(
        Settings(api_keys="test-suite", postgres_db=database).database_url
    )


async def _with_session(database: str, scenario) -> Any:
    engine = _engine(database)
    try:
        async with AsyncSession(engine) as session:
            return await scenario(session)
    finally:
        await engine.dispose()


def _counts(database: str) -> int:
    async def count(session: AsyncSession) -> int:
        return (await session.execute(select(func.count(TelegramUpdate.update_id)))).scalar_one()

    return asyncio.run(_with_session(database, count))


@pytest.fixture(autouse=True)
def _clean_table(migrated_test_db: str) -> None:
    """Each test starts from an empty table (the per-worker DB is shared)."""

    async def wipe(session: AsyncSession) -> None:
        await session.execute(delete(TelegramUpdate))
        await session.commit()

    asyncio.run(_with_session(migrated_test_db, wipe))


def test_first_claim_returns_true_and_stores_row(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> bool:
        return await claim_update(session, OWNER_TEXT)

    assert asyncio.run(_with_session(migrated_test_db, scenario)) is True

    async def row(session: AsyncSession) -> TelegramUpdate:
        return await session.get_one(TelegramUpdate, OWNER_TEXT.update_id)

    stored = asyncio.run(_with_session(migrated_test_db, row))
    assert stored.chat_id == 111111
    assert stored.message_id == 101
    assert stored.kind == "text"
    assert stored.status == "received"
    assert stored.route == ""


def test_second_claim_returns_false_and_keeps_one_row(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> tuple[bool, bool]:
        first = await claim_update(session, OWNER_TEXT)
        second = await claim_update(session, OWNER_TEXT)
        return first, second

    first, second = asyncio.run(_with_session(migrated_test_db, scenario))
    assert first is True
    assert second is False
    assert _counts(migrated_test_db) == 1


def test_concurrent_claims_yield_exactly_one_true(migrated_test_db: str) -> None:
    async def scenario() -> list[bool]:
        engine = _engine(migrated_test_db)
        try:
            async with AsyncSession(engine) as s1, AsyncSession(engine) as s2:
                return await asyncio.gather(
                    claim_update(s1, OWNER_TEXT), claim_update(s2, OWNER_TEXT)
                )
        finally:
            await engine.dispose()

    results = asyncio.run(scenario())
    assert sorted(results) == [False, True]
    assert _counts(migrated_test_db) == 1


def test_mark_update_sets_status_and_route(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> TelegramUpdate:
        await claim_update(session, OWNER_TEXT)
        await mark_update(session, OWNER_TEXT.update_id, "processed", "core.help")
        return await session.get_one(TelegramUpdate, OWNER_TEXT.update_id)

    stored = asyncio.run(_with_session(migrated_test_db, scenario))
    assert stored.status == "processed"
    assert stored.route == "core.help"


def test_mark_unknown_update_is_noop(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> None:
        await mark_update(session, SECOND_ID, "processed")

    asyncio.run(_with_session(migrated_test_db, scenario))  # no error
    assert _counts(migrated_test_db) == 0


def test_delete_updates_before_removes_only_older_rows(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> int:
        await claim_update(session, OWNER_TEXT)
        await claim_update(session, to_inbound(load_update("voice")))
        # Age only the first row beyond the cutoff.
        old = datetime.now(timezone.utc) - timedelta(days=31)
        await session.execute(
            update(TelegramUpdate)
            .where(TelegramUpdate.update_id == OWNER_TEXT.update_id)
            .values(received_at=old)
        )
        await session.commit()
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        return await delete_updates_before(session, cutoff)

    deleted = asyncio.run(_with_session(migrated_test_db, scenario))
    assert deleted == 1
    assert _counts(migrated_test_db) == 1
