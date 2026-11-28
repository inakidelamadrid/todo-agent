"""Protected /tasks routes.

Thin layer: validate → repository → schema. Mounted with
``dependencies=[Depends(require_principal)]`` in ``app/main.py``.
"""

from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi import status as http_status
from pydantic import BaseModel, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.tasks import repository
from app.tasks.domain import TaskEvent, transition
from app.tasks.models import Task
from app.tasks.repository import ParentProblem
from app.tasks.schemas import TaskCreate, TaskOut, TaskStatus, TaskUpdate

Session = Annotated[AsyncSession, Depends(get_session)]


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


class _SnoozeBody(BaseModel):
    until: date

    @model_validator(mode="after")
    def _until_must_be_future(self):
        if self.until <= datetime.now(UTC).date():
            raise ValueError("Snooze date must be in the future")
        return self


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found"
    )


async def _task_or_404(session: AsyncSession, task_id: UUID) -> Task:
    task = await repository.get_task(session, task_id)
    if task is None:
        raise _not_found()
    return task


@tasks_router.get(
    "",
    response_model=list[TaskOut],
    summary="List top-level tasks (use parentId to list children)",
)
async def list_tasks(
    session: Session,
    status: Annotated[list[TaskStatus] | None, Query()] = None,
    parent_id: Annotated[UUID | None, Query(alias="parentId")] = None,
) -> list[Task]:
    statuses = status if status else (TaskStatus.ACTIVE, TaskStatus.SNOOZED)
    return await repository.list_tasks(session, statuses=tuple(statuses), parent_id=parent_id)


@tasks_router.post("", status_code=http_status.HTTP_201_CREATED, summary="Create a task")
async def create_task(session: Session, data: TaskCreate, response: Response) -> TaskOut:
    result = await repository.create_task(session, data)
    if result == ParentProblem.NOT_FOUND:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parent task not found",
        )
    if result == ParentProblem.TOO_DEEP:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subtasks can only be one level deep",
        )
    response.headers["Location"] = f"/tasks/{result.id}"
    return TaskOut.model_validate(result)


@tasks_router.get("/{task_id}", response_model=TaskOut, summary="Get one task")
async def get_task(session: Session, task_id: UUID) -> TaskOut:
    return TaskOut.model_validate(await _task_or_404(session, task_id))


@tasks_router.patch("/{task_id}", response_model=TaskOut, summary="Partially update a task")
async def update_task(session: Session, task_id: UUID, patch: TaskUpdate) -> TaskOut:
    task = await _task_or_404(session, task_id)
    return TaskOut.model_validate(await repository.update_task(session, task, patch))


@tasks_router.delete(
    "/{task_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete a task and its subtasks",
)
async def delete_task(session: Session, task_id: UUID) -> None:
    task = await _task_or_404(session, task_id)
    await repository.delete_task(session, task)


@tasks_router.post(
    "/{task_id}/complete",
    response_model=TaskOut,
    summary="Mark a task as done",
)
async def complete_task(session: Session, task_id: UUID) -> TaskOut:
    return await _act(session, task_id, TaskEvent.COMPLETE)


@tasks_router.post(
    "/{task_id}/snooze",
    response_model=TaskOut,
    summary="Snooze a task until a date",
)
async def snooze_task(
    session: Session, task_id: UUID, body: _SnoozeBody
) -> TaskOut:
    return await _act(session, task_id, TaskEvent.SNOOZE, snoozed_until=body.until)


@tasks_router.post(
    "/{task_id}/drop",
    response_model=TaskOut,
    summary="Mark a task as dropped",
)
async def drop_task(session: Session, task_id: UUID) -> TaskOut:
    return await _act(session, task_id, TaskEvent.DROP)


@tasks_router.post(
    "/{task_id}/reopen",
    response_model=TaskOut,
    summary="Reopen a done or dropped task",
)
async def reopen_task(session: Session, task_id: UUID) -> TaskOut:
    return await _act(session, task_id, TaskEvent.REOPEN)


async def _act(
    session: AsyncSession,
    task_id: UUID,
    event: TaskEvent,
    *,
    snoozed_until: date | None = None,
) -> TaskOut:
    task = await _task_or_404(session, task_id)
    new_status = transition(TaskStatus(task.status), event)
    if new_status is None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Can't {event.value} a task that is {task.status}",
        )
    updated = await repository.apply_status(
        session,
        task,
        new_status,
        snoozed_until=snoozed_until,
    )
    return TaskOut.model_validate(updated)
