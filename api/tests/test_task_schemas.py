"""Tests for task schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.tasks.schemas import (
    Energy,
    TaskContext,
    TaskCreate,
    TaskOut,
    TaskSize,
    TaskStatus,
    TaskUpdate,
)


def test_create_defaults_size_energy_context():
    task = TaskCreate(title="  Call dentist ")
    assert task.title == "Call dentist"
    assert task.size == TaskSize.S
    assert task.energy == Energy.MEDIUM
    assert task.context == TaskContext.ANYWHERE
    assert task.notes == ""
    assert task.do_date is None
    assert task.due_date is None
    assert task.first_step == ""
    assert task.parent_id is None
    assert task.created_from is None


def test_title_is_trimmed_and_required():
    with pytest.raises(ValidationError):
        TaskCreate(title="  ")
    with pytest.raises(ValidationError):
        TaskCreate(title="")


def test_title_longer_than_120_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="x" * 121)


def test_unknown_size_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="x", size="XXL")


def test_update_rejects_status_and_parent_id():
    with pytest.raises(ValidationError):
        TaskUpdate(status="done")
    with pytest.raises(ValidationError):
        TaskUpdate(parent_id="00000000-0000-0000-0000-000000000000")


def test_update_rejects_unknown_field():
    with pytest.raises(ValidationError):
        TaskUpdate(unknown="nope")


def test_update_rejects_explicit_null_on_non_clearable_fields():
    for field in ("title", "notes", "size", "energy", "context", "first_step"):
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(**{field: None})
        assert "cannot be set to null" in str(exc_info.value)


def test_update_allows_null_on_clearable_fields():
    patch = TaskUpdate(do_date=None, due_date=None)
    assert patch.do_date is None
    assert patch.due_date is None


def test_out_serialises_camel_case():
    now = datetime.now(UTC)
    out = TaskOut(
        id=uuid4(),
        title="Call dentist",
        notes="",
        size=TaskSize.S,
        energy=Energy.LOW,
        context=TaskContext.PHONE,
        do_date=None,
        due_date=None,
        first_step="Find the number",
        parent_id=None,
        created_from=None,
        status=TaskStatus.ACTIVE,
        snoozed_until=None,
        completed_at=None,
        dropped_at=None,
        created_at=now,
        updated_at=now,
    )
    dumped = out.model_dump(by_alias=True)
    assert dumped["firstStep"] == "Find the number"
    assert dumped["parentId"] is None
    assert dumped["createdFrom"] is None
    assert dumped["snoozedUntil"] is None
    assert dumped["completedAt"] is None
    assert dumped["droppedAt"] is None
    assert "first_step" not in dumped
