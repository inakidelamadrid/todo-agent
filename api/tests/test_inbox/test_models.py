"""Tests for dumps/inbox_items table structure (BE-092)."""

import asyncio

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.settings import Settings


def test_inbox_items_has_dump_fk_with_cascade(migrated_test_db: str):
    async def _check():
        engine = create_async_engine(
            Settings(api_keys="test-suite", postgres_db=migrated_test_db).database_url
        )
        async with engine.connect() as conn:
            fks = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_foreign_keys("inbox_items"))
        await engine.dispose()
        return fks

    fks = asyncio.run(_check())
    dump_fk = next(fk for fk in fks if fk["referred_table"] == "dumps")
    assert dump_fk["options"].get("ondelete") == "CASCADE"
