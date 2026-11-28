"""Tests for task model constraints."""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings


def _engine(database: str):
    return create_async_engine(
        Settings(api_keys="test-suite", postgres_db=database).database_url
    )


async def _with_session(database: str, scenario):
    engine = _engine(database)
    try:
        async with AsyncSession(engine) as session:
            return await scenario(session)
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tasks(migrated_test_db: str):
    async def wipe(session: AsyncSession):
        await session.execute(text("DELETE FROM tasks"))
        await session.commit()

    asyncio.run(_with_session(migrated_test_db, wipe))


def test_tasks_check_rejects_empty_title(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        await session.execute(
            text(
                "INSERT INTO tasks (title, size, energy, context, status, notes, first_step) "
                "VALUES ('', 'S', 'low', 'phone', 'active', '', '')"
            )
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        asyncio.run(_with_session(migrated_test_db, scenario))


def test_snoozed_requires_snoozed_until(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        await session.execute(
            text(
                "INSERT INTO tasks (title, size, energy, context, status, snoozed_until, notes, first_step) "
                "VALUES ('x', 'S', 'low', 'phone', 'snoozed', NULL, '', '')"
            )
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        asyncio.run(_with_session(migrated_test_db, scenario))


def test_deleting_parent_cascades_to_children(migrated_test_db: str):
    from uuid import uuid4

    parent_id = uuid4()
    child_id = uuid4()

    async def scenario(session: AsyncSession):
        await session.execute(
            text(
                "INSERT INTO tasks (id, title, notes, first_step, size, energy, context, status) "
                "VALUES (:id, 'Parent', '', '', 'S', 'low', 'phone', 'active')"
            ),
            {"id": parent_id},
        )
        await session.execute(
            text(
                "INSERT INTO tasks (id, parent_id, title, notes, first_step, size, energy, context, status) "
                "VALUES (:id, :parent_id, 'Child', '', '', 'S', 'low', 'phone', 'active')"
            ),
            {"id": child_id, "parent_id": parent_id},
        )
        await session.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": parent_id})
        await session.commit()
        result = await session.execute(text("SELECT count(*) FROM tasks"))
        return result.scalar_one()

    count = asyncio.run(_with_session(migrated_test_db, scenario))
    assert count == 0
