"""Tests for the task repository."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.tasks.models import Task
from app.tasks.repository import (
    ParentProblem,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from app.tasks.schemas import TaskCreate, TaskSize, TaskStatus, TaskUpdate


@pytest.fixture(autouse=True)
def _clean_tasks(migrated_test_db: str):
    async def wipe(session: AsyncSession):
        await session.execute(delete(Task))
        await session.commit()

    asyncio.run(_with_session(migrated_test_db, wipe))


def _engine(database: str):
    return create_async_engine(
        Settings(api_keys="test-suite", postgres_db=database).database_url
    )


async def _with_session(database: str, scenario):
    engine = _engine(database)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            return await scenario(session)
    finally:
        await engine.dispose()


async def _create(database: str, data: TaskCreate) -> Task:
    result = await _with_session(
        database,
        lambda session: create_task(session, data),
    )
    assert isinstance(result, Task), result
    return result


def test_list_defaults_to_active_and_snoozed(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        await create_task(session, TaskCreate(title="Parent task"))
        done = await create_task(session, TaskCreate(title="Done task"))
        done.status = TaskStatus.DONE.value
        await session.commit()
        return await list_tasks(session)

    items = asyncio.run(_with_session(migrated_test_db, scenario))
    assert len(items) == 1
    assert items[0].title == "Parent task"


def test_list_orders_by_due_then_do_date(migrated_test_db: str):
    from datetime import date

    async def scenario(session: AsyncSession):
        await create_task(session, TaskCreate(title="A", due_date=date(2026, 12, 1)))
        await create_task(session, TaskCreate(title="B", due_date=date(2026, 11, 1)))
        await create_task(session, TaskCreate(title="C", do_date=date(2026, 10, 1)))
        await session.commit()
        return await list_tasks(session, statuses=(TaskStatus.ACTIVE, TaskStatus.SNOOZED))

    items = asyncio.run(_with_session(migrated_test_db, scenario))
    assert [item.title for item in items] == ["B", "A", "C"]


def test_list_children_of_parent(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        parent = await create_task(session, TaskCreate(title="Parent task"))
        parent_id = parent.id
        await create_task(session, TaskCreate(title="Subtask", parent_id=parent_id))
        await create_task(session, TaskCreate(title="Other"))
        await session.commit()
        return await list_tasks(session, parent_id=parent_id)

    items = asyncio.run(_with_session(migrated_test_db, scenario))
    assert len(items) == 1
    assert items[0].title == "Subtask"


def test_get_missing_returns_none(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        return await get_task(session, uuid4())

    assert asyncio.run(_with_session(migrated_test_db, scenario)) is None


def test_create_task_starts_active(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        return await create_task(session, TaskCreate(title="New task"))

    task = asyncio.run(_with_session(migrated_test_db, scenario))
    assert task.status == TaskStatus.ACTIVE.value


def test_create_subtask_of_top_level_task(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        parent = await create_task(session, TaskCreate(title="Parent task"))
        parent_id = parent.id
        sub = await create_task(session, TaskCreate(title="Subtask", parent_id=parent_id))
        return parent_id, sub

    parent_id, sub = asyncio.run(_with_session(migrated_test_db, scenario))
    assert sub.parent_id == parent_id
    assert sub.status == TaskStatus.ACTIVE.value


def test_rejects_missing_parent(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        return await create_task(session, TaskCreate(title="Orphan", parent_id=uuid4()))

    result = asyncio.run(_with_session(migrated_test_db, scenario))
    assert result == ParentProblem.NOT_FOUND


def test_rejects_grandchild_task(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        parent = await create_task(session, TaskCreate(title="Parent task"))
        parent_id = parent.id
        sub = await create_task(session, TaskCreate(title="Subtask", parent_id=parent_id))
        return await create_task(session, TaskCreate(title="Grandchild", parent_id=sub.id))

    result = asyncio.run(_with_session(migrated_test_db, scenario))
    assert result == ParentProblem.TOO_DEEP


def test_update_changes_only_sent_fields(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        task = await create_task(session, TaskCreate(title="Original"))
        task_id = task.id
        await session.commit()
        refreshed = await get_task(session, task_id)
        updated = await update_task(session, refreshed, TaskUpdate(title="Renamed"))
        await session.commit()
        return updated

    updated = asyncio.run(_with_session(migrated_test_db, scenario))
    assert updated.title == "Renamed"
    assert updated.size == TaskSize.S.value


def test_delete_removes_children(migrated_test_db: str):
    async def scenario(session: AsyncSession):
        parent = await create_task(session, TaskCreate(title="Parent task"))
        parent_id = parent.id
        await create_task(session, TaskCreate(title="Subtask", parent_id=parent_id))
        await session.commit()
        refreshed = await get_task(session, parent_id)
        await delete_task(session, refreshed)
        await session.commit()
        return await get_task(session, parent_id)

    result = asyncio.run(_with_session(migrated_test_db, scenario))
    assert result is None
