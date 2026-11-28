"""SQLAlchemy ORM tables for dumps and inbox items."""

import uuid
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.inbox.schemas import Confidence, DumpSource, ItemStatus, ItemType
from app.tasks.schemas import Energy, TaskContext, TaskSize

RAW_TEXT_MAX = 4000
SUMMARY_MAX = 120
NOTE_BODY_MAX = 2000
CURRENCY_MAX_LEN = 3
ITEM_STATUS_MAX = 12
FIRST_STEP_MAX = 200
SIZE_MAX = 2
ENERGY_MAX = 10
CONTEXT_MAX = 10


class Dump(Base):
    __tablename__ = "dumps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    raw_text: Mapped[str] = mapped_column(String(RAW_TEXT_MAX))
    source: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            f"source IN {tuple(s.value for s in DumpSource)}",
            name="ck_dumps_source",
        ),
        CheckConstraint(
            f"char_length(raw_text) BETWEEN 1 AND {RAW_TEXT_MAX}",
            name="ck_dumps_raw_text_len",
        ),
        Index("ix_dumps_created_at", "created_at"),
    )


class InboxItem(Base):
    __tablename__ = "inbox_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dump_id: Mapped[UUID] = mapped_column(
        ForeignKey("dumps.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(ITEM_STATUS_MAX), default=ItemStatus.NEW.value)
    summary: Mapped[str] = mapped_column(String(SUMMARY_MAX))
    confidence: Mapped[str] = mapped_column(String(10))
    size: Mapped[str | None] = mapped_column(String(SIZE_MAX))
    energy: Mapped[str | None] = mapped_column(String(ENERGY_MAX))
    context: Mapped[str | None] = mapped_column(String(CONTEXT_MAX))
    first_step: Mapped[str | None] = mapped_column(String(FIRST_STEP_MAX))
    body: Mapped[str | None] = mapped_column(String(NOTE_BODY_MAX))
    amount_cents: Mapped[int | None]
    currency: Mapped[str | None] = mapped_column(String(CURRENCY_MAX_LEN))
    do_date: Mapped[date | None]
    due_date: Mapped[date | None]
    snoozed_until: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            f"type IN {tuple(t.value for t in ItemType)}",
            name="ck_inbox_items_type",
        ),
        CheckConstraint(
            f"confidence IN {tuple(c.value for c in Confidence)}",
            name="ck_inbox_items_confidence",
        ),
        CheckConstraint(
            f"status IN {tuple(s.value for s in ItemStatus)}",
            name="ck_inbox_items_status",
        ),
        CheckConstraint(
            f"char_length(summary) BETWEEN 1 AND {SUMMARY_MAX}",
            name="ck_inbox_items_summary_len",
        ),
        CheckConstraint(
            f"size IS NULL OR size IN {tuple(s.value for s in TaskSize)}",
            name="ck_inbox_items_size",
        ),
        CheckConstraint(
            f"energy IS NULL OR energy IN {tuple(e.value for e in Energy)}",
            name="ck_inbox_items_energy",
        ),
        CheckConstraint(
            f"context IS NULL OR context IN {tuple(c.value for c in TaskContext)}",
            name="ck_inbox_items_context",
        ),
        CheckConstraint(
            f"first_step IS NULL OR char_length(first_step) <= {FIRST_STEP_MAX}",
            name="ck_inbox_items_first_step_len",
        ),
        Index("ix_inbox_items_dump_id", "dump_id"),
        Index("ix_inbox_items_created_at", "created_at"),
        Index("ix_inbox_items_status", "status"),
    )
