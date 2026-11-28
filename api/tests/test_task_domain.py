"""Tests for task domain rules."""

from datetime import date

import pytest

from app.tasks.domain import SIZE_MINUTES, is_awake, transition
from app.tasks.schemas import TaskEvent, TaskSize, TaskStatus

LEGAL_TRANSITIONS = [
    (TaskStatus.ACTIVE, TaskEvent.COMPLETE, TaskStatus.DONE),
    (TaskStatus.ACTIVE, TaskEvent.SNOOZE, TaskStatus.SNOOZED),
    (TaskStatus.ACTIVE, TaskEvent.DROP, TaskStatus.DROPPED),
    (TaskStatus.SNOOZED, TaskEvent.COMPLETE, TaskStatus.DONE),
    (TaskStatus.SNOOZED, TaskEvent.SNOOZE, TaskStatus.SNOOZED),
    (TaskStatus.SNOOZED, TaskEvent.WAKE, TaskStatus.ACTIVE),
    (TaskStatus.SNOOZED, TaskEvent.DROP, TaskStatus.DROPPED),
    (TaskStatus.DONE, TaskEvent.REOPEN, TaskStatus.ACTIVE),
    (TaskStatus.DROPPED, TaskEvent.REOPEN, TaskStatus.ACTIVE),
]


@pytest.mark.parametrize("status, event, expected", LEGAL_TRANSITIONS)
def test_legal_transition(status, event, expected):
    assert transition(status, event) == expected


ILLEGAL_TRANSITIONS = [
    (TaskStatus.ACTIVE, TaskEvent.WAKE),
    (TaskStatus.ACTIVE, TaskEvent.REOPEN),
    (TaskStatus.SNOOZED, TaskEvent.REOPEN),
    (TaskStatus.DONE, TaskEvent.SNOOZE),
    (TaskStatus.DONE, TaskEvent.WAKE),
    (TaskStatus.DONE, TaskEvent.DROP),
    (TaskStatus.DROPPED, TaskEvent.COMPLETE),
    (TaskStatus.DROPPED, TaskEvent.SNOOZE),
]


@pytest.mark.parametrize("status, event", ILLEGAL_TRANSITIONS)
def test_illegal_transitions_return_none(status, event):
    assert transition(status, event) is None


def test_size_minutes_xl_is_none():
    assert SIZE_MINUTES[TaskSize.XL] is None


def test_size_minutes_values():
    assert SIZE_MINUTES[TaskSize.XS] == 5
    assert SIZE_MINUTES[TaskSize.S] == 15
    assert SIZE_MINUTES[TaskSize.M] == 45
    assert SIZE_MINUTES[TaskSize.L] == 120


def test_snoozed_task_wakes_on_its_date():
    today = date(2026, 11, 28)
    assert is_awake(TaskStatus.SNOOZED, today, today) is True


def test_snoozed_task_sleeps_before_its_date():
    today = date(2026, 11, 27)
    wake = date(2026, 11, 28)
    assert is_awake(TaskStatus.SNOOZED, wake, today) is False


def test_active_is_always_awake():
    today = date(2026, 11, 28)
    assert is_awake(TaskStatus.ACTIVE, None, today) is True


def test_done_and_dropped_are_not_awake():
    today = date(2026, 11, 28)
    assert is_awake(TaskStatus.DONE, None, today) is False
    assert is_awake(TaskStatus.DROPPED, None, today) is False
