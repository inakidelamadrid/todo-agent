"""SQLAlchemy ORM table for tasks.

CHECK constraints mirror the API validation rules so the database enforces
the same contract even outside the app.
"""

import uuid
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.tasks.schemas import (
    FIRST_STEP_MAX,
    NOTES_MAX,
    TITLE_MAX,
    Energy,
    TaskContext,
    TaskSize,
    TaskStatus,
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(TITLE_MAX))
    notes: Mapped[str] = mapped_column(String(NOTES_MAX), default="")
    size: Mapped[str] = mapped_column(String(2))
    energy: Mapped[str] = mapped_column(String(10))
    context: Mapped[str] = mapped_column(String(10))
    do_date: Mapped[date | None]
    due_date: Mapped[date | None]
    first_step: Mapped[str] = mapped_column(String(FIRST_STEP_MAX), default="")
    # Links to an inbox item once BE-089 lands; the FK is added there.
    created_from: Mapped[UUID | None]
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(10))
    snoozed_until: Mapped[date | None]
    completed_at: Mapped[datetime | None]
    dropped_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(f"char_length(title) BETWEEN 1 AND {TITLE_MAX}", name="ck_tasks_title_len"),
        CheckConstraint(f"char_length(notes) <= {NOTES_MAX}", name="ck_tasks_notes_len"),
        CheckConstraint(f"size IN {tuple(e.value for e in TaskSize)}", name="ck_tasks_size"),
        CheckConstraint(f"energy IN {tuple(e.value for e in Energy)}", name="ck_tasks_energy"),
        CheckConstraint(f"context IN {tuple(e.value for e in TaskContext)}", name="ck_tasks_context"),
        CheckConstraint(f"status IN {tuple(e.value for e in TaskStatus)}", name="ck_tasks_status"),
        CheckConstraint(f"char_length(first_step) <= {FIRST_STEP_MAX}", name="ck_tasks_first_step_len"),
        CheckConstraint("parent_id IS NULL OR parent_id != id", name="ck_tasks_no_self_parent"),
        CheckConstraint(
            "status != 'snoozed' OR snoozed_until IS NOT NULL",
            name="ck_tasks_snoozed_requires_date",
        ),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_parent_id", "parent_id"),
        Index("ix_tasks_due_date", "due_date"),
    )
