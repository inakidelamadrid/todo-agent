"""API schemas for brain-dump inbox.

Frozen Pydantic models, snake_case internally, camelCase on the wire.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.tasks.schemas import Energy, TaskContext, TaskSize

RAW_TEXT_MAX = 4000
SUMMARY_MAX = 120
NOTE_BODY_MAX = 2000
CURRENCY_MAX_LEN = 3


class DumpSource(StrEnum):
    WEB = "web"
    TELEGRAM = "telegram"
    N8N = "n8n"


class ItemType(StrEnum):
    TASK = "task"
    REMINDER = "reminder"
    NOTE = "note"
    EXPENSE = "expense"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ItemStatus(StrEnum):
    NEW = "new"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"
    SNOOZED = "snoozed"


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )


def _strip(value: str) -> str:
    return value.strip()


class DumpIn(_CamelModel):
    raw_text: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=RAW_TEXT_MAX)]
    source: DumpSource = DumpSource.WEB
    context: TaskContext | None = None


class TaskCandidate(_CamelModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ItemType.TASK] = ItemType.TASK
    summary: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=SUMMARY_MAX)]
    size: TaskSize = TaskSize.S
    energy: Energy = Energy.MEDIUM
    context: TaskContext = TaskContext.ANYWHERE
    do_date: date | None = None
    due_date: date | None = None
    first_step: Annotated[str, AfterValidator(_strip), Field(max_length=200)] = ""
    confidence: Confidence = Confidence.MEDIUM


class ReminderCandidate(_CamelModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ItemType.REMINDER] = ItemType.REMINDER
    summary: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=SUMMARY_MAX)]
    do_date: date
    confidence: Confidence = Confidence.MEDIUM


class NoteCandidate(_CamelModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ItemType.NOTE] = ItemType.NOTE
    summary: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=SUMMARY_MAX)]
    body: Annotated[str, AfterValidator(_strip), Field(max_length=NOTE_BODY_MAX)] = ""
    confidence: Confidence = Confidence.MEDIUM


class ExpenseCandidate(_CamelModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ItemType.EXPENSE] = ItemType.EXPENSE
    summary: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=SUMMARY_MAX)]
    amount_cents: Annotated[int, Field(ge=0, le=1_000_000_000)]
    currency: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=CURRENCY_MAX_LEN)]
    confidence: Confidence = Confidence.MEDIUM


CandidateItem = Annotated[
    TaskCandidate | ReminderCandidate | NoteCandidate | ExpenseCandidate,
    Field(discriminator="type"),
]


class ParseDumpResult(_CamelModel):
    model_config = ConfigDict(frozen=True)

    items: tuple[CandidateItem, ...]

    @model_validator(mode="after")
    def _items_not_empty(self):
        if not self.items:
            raise ValueError("Parse result must contain at least one item")
        return self


class InboxItemOut(_CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dump_id: UUID
    type: ItemType
    status: ItemStatus
    summary: str
    confidence: Confidence
    size: TaskSize | None
    energy: Energy | None
    context: TaskContext | None
    first_step: str | None
    body: str | None
    amount_cents: int | None
    currency: str | None
    do_date: date | None
    due_date: date | None
    snoozed_until: date | None
    created_at: datetime


class DumpOut(_CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_text: str
    source: DumpSource
    created_at: datetime
