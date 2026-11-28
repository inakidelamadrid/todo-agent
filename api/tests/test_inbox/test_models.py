"""Tests for dumps/inbox_items table structure (BE-092)."""

import asyncio
from datetime import date

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.inbox.models import Dump, InboxItem
from app.inbox.schemas import Confidence, DumpSource, InboxItemOut, ItemStatus, ItemType
from app.settings import Settings


def test_inbox_items_has_dump_fk_with_cascade(migrated_test_db: str):
    async def _check():
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=migrated_test_db).database_url
        )
        async with engine.connect() as conn:
            fks = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_foreign_keys("inbox_items")
            )
        await engine.dispose()
        return fks

    fks = asyncio.run(_check())
    dump_fk = next(fk for fk in fks if fk["referred_table"] == "dumps")
    assert dump_fk["options"].get("ondelete") == "CASCADE"


def test_snoozed_until_is_a_date_not_datetime(migrated_test_db: str):
    """Regression: a non-midnight timestamp used to fail InboxItemOut validation."""

    async def _check():
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=migrated_test_db).database_url
        )
        async with AsyncSession(engine, expire_on_commit=False) as session:
            dump = Dump(raw_text="snooze test", source=DumpSource.WEB.value)
            session.add(dump)
            await session.flush()

            item = InboxItem(
                dump_id=dump.id,
                type=ItemType.TASK.value,
                status=ItemStatus.SNOOZED.value,
                summary="Snoozed task",
                confidence=Confidence.LOW.value,
                snoozed_until=date(2026, 12, 1),
            )
            session.add(item)
            await session.commit()

            loaded = await session.get(InboxItem, item.id)
            assert loaded is not None
            assert isinstance(loaded.snoozed_until, date)
            out = InboxItemOut.model_validate(loaded)
            assert out.snoozed_until.isoformat() == "2026-12-01"

            await session.delete(loaded)
            await session.delete(dump)
            await session.commit()
        await engine.dispose()

    asyncio.run(_check())
