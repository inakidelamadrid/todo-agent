"""Async persistence for tasks.

Functions take a session and do exactly one thing. No HTTP, no FastAPI.
"""

from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.models import Task
from app.tasks.schemas import TaskCreate, TaskStatus, TaskUpdate


class ParentProblem(StrEnum):
    NOT_FOUND = "parent-not-found"
    TOO_DEEP = "parent-is-a-subtask"


async def list_tasks(
    session: AsyncSession,
    statuses: tuple[TaskStatus, ...] = (TaskStatus.ACTIVE, TaskStatus.SNOOZED),
    parent_id: UUID | None = None,
) -> list[Task]:
    stmt = select(Task).where(Task.status.in_(status.value for status in statuses))
    if parent_id is not None:
        stmt = stmt.where(Task.parent_id == parent_id)
    else:
        stmt = stmt.where(Task.parent_id.is_(None))
    stmt = stmt.order_by(
        Task.due_date.asc().nulls_last(),
        Task.do_date.asc().nulls_last(),
        Task.created_at,
        Task.id,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_task(session: AsyncSession, task_id: UUID) -> Task | None:
    return await session.get(Task, task_id)


async def create_task(session: AsyncSession, data: TaskCreate) -> Task | ParentProblem:
    parent_id = data.parent_id
    if parent_id is not None:
        parent = await get_task(session, parent_id)
        if parent is None:
            return ParentProblem.NOT_FOUND
        if parent.parent_id is not None:
            return ParentProblem.TOO_DEEP

    task = Task(**data.model_dump(), status=TaskStatus.ACTIVE.value)
    session.add(task)
    await session.flush()
    return task


async def update_task(session: AsyncSession, task: Task, patch: TaskUpdate) -> Task:
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await session.flush()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
