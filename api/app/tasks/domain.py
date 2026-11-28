"""Pure domain logic for tasks.

State machine, size minutes, and snooze rules. No I/O, no FastAPI, no
SQLAlchemy.
"""

from collections.abc import Mapping
from datetime import date
from types import MappingProxyType

from app.tasks.schemas import TaskEvent, TaskSize, TaskStatus

TRANSITIONS: Mapping[tuple[TaskStatus, TaskEvent], TaskStatus] = MappingProxyType(
    {
        (TaskStatus.ACTIVE, TaskEvent.COMPLETE): TaskStatus.DONE,
        (TaskStatus.ACTIVE, TaskEvent.SNOOZE): TaskStatus.SNOOZED,
        (TaskStatus.ACTIVE, TaskEvent.DROP): TaskStatus.DROPPED,
        (TaskStatus.SNOOZED, TaskEvent.COMPLETE): TaskStatus.DONE,
        (TaskStatus.SNOOZED, TaskEvent.SNOOZE): TaskStatus.SNOOZED,
        (TaskStatus.SNOOZED, TaskEvent.WAKE): TaskStatus.ACTIVE,
        (TaskStatus.SNOOZED, TaskEvent.DROP): TaskStatus.DROPPED,
        (TaskStatus.DONE, TaskEvent.REOPEN): TaskStatus.ACTIVE,
        (TaskStatus.DROPPED, TaskEvent.REOPEN): TaskStatus.ACTIVE,
    }
)

SIZE_MINUTES: Mapping[TaskSize, int | None] = MappingProxyType(
    {
        TaskSize.XS: 5,
        TaskSize.S: 15,
        TaskSize.M: 45,
        TaskSize.L: 120,
        TaskSize.XL: None,
    }
)


def transition(status: TaskStatus, event: TaskEvent) -> TaskStatus | None:
    """Return the new status, or None if the event is illegal from status."""
    return TRANSITIONS.get((status, event))


def is_awake(status: TaskStatus, snoozed_until: date | None, today: date) -> bool:
    """True if the task should be shown as actionable today."""
    if status == TaskStatus.ACTIVE:
        return True
    if status == TaskStatus.SNOOZED:
        return snoozed_until is not None and snoozed_until <= today
    return False
