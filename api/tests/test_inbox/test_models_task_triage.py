"""Tests that task triage columns round-trip through the DB."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.inbox.domain import drafts_from_result, fallback_result
from app.inbox.models import Dump, InboxItem
from app.inbox.schemas import (
    DumpSource,
    Energy,
    InboxItemOut,
    TaskContext,
    TaskSize,
)
from app.settings import Settings


def test_task_triage_columns_round_trip(migrated_test_db: str):
    async def _check():
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=migrated_test_db).database_url
        )
        async with AsyncSession(engine, expire_on_commit=False) as session:
            dump = Dump(raw_text="test", source=DumpSource.WEB.value)
            session.add(dump)
            await session.flush()

            drafts = drafts_from_result(dump.id, fallback_result("call dentist"))
            for draft in drafts:
                item = InboxItem(**draft)
                session.add(item)
            await session.commit()

            loaded = await session.get(InboxItem, item.id)
            assert loaded is not None
            assert loaded.size == TaskSize.S.value
            assert loaded.energy == Energy.MEDIUM.value
            assert loaded.context == TaskContext.ANYWHERE.value
            assert loaded.first_step == ""

            out = InboxItemOut.model_validate(loaded)
            assert out.size == TaskSize.S
            assert out.energy == Energy.MEDIUM
            assert out.context == TaskContext.ANYWHERE
            assert out.first_step == ""

            await session.delete(dump)
            await session.commit()
        await engine.dispose()

    asyncio.run(_check())
