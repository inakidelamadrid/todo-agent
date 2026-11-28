"""API schemas for tasks.

Frozen Pydantic models, snake_case internally, camelCase on the wire.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

TITLE_MAX = 120
NOTES_MAX = 2000
FIRST_STEP_MAX = 200


class TaskSize(StrEnum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class Energy(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskContext(StrEnum):
    HOME = "home"
    COMPUTER = "computer"
    PHONE = "phone"
    ERRAND = "errand"
    ANYWHERE = "anywhere"


class TaskStatus(StrEnum):
    ACTIVE = "active"
    SNOOZED = "snoozed"
    DONE = "done"
    DROPPED = "dropped"


class TaskEvent(StrEnum):
    COMPLETE = "complete"
    SNOOZE = "snooze"
    WAKE = "wake"
    DROP = "drop"
    REOPEN = "reopen"


def _strip(value: str) -> str:
    return value.strip()


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )


class TaskCreate(_CamelModel):
    title: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=TITLE_MAX)]
    notes: Annotated[str, Field(max_length=NOTES_MAX)] = ""
    size: TaskSize = TaskSize.S
    energy: Energy = Energy.MEDIUM
    context: TaskContext = TaskContext.ANYWHERE
    do_date: date | None = None
    due_date: date | None = None
    first_step: Annotated[str, AfterValidator(_strip), Field(max_length=FIRST_STEP_MAX)] = ""
    parent_id: UUID | None = None
    created_from: UUID | None = None


class TaskUpdate(_CamelModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=TITLE_MAX)] | None = None
    notes: Annotated[str, Field(max_length=NOTES_MAX)] | None = None
    size: TaskSize | None = None
    energy: Energy | None = None
    context: TaskContext | None = None
    do_date: date | None = None
    due_date: date | None = None
    first_step: Annotated[str, AfterValidator(_strip), Field(max_length=FIRST_STEP_MAX)] | None = None

    @model_validator(mode="after")
    def _no_explicit_null_on_non_clearable_fields(self):
        for field in ("title", "notes", "size", "energy", "context", "first_step"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be set to null")
        return self


class TaskOut(_CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    notes: str
    size: TaskSize
    energy: Energy
    context: TaskContext
    do_date: date | None
    due_date: date | None
    first_step: str
    parent_id: UUID | None
    created_from: UUID | None
    status: TaskStatus
    snoozed_until: date | None
    completed_at: datetime | None
    dropped_at: datetime | None
    created_at: datetime
    updated_at: datetime
