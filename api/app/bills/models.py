"""SQLAlchemy ORM tables for bills and payments.

CHECK constraints mirror the API validation rules so the database enforces
the same contract even outside the app. Money is integer cents, always.
"""

import uuid
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.bills.schemas import MAX_CENTS, Currency, Line, Recurrence
from app.db import Base

_MONTH_SQL_RE = "^\\d{4}-(0[1-9]|1[0-2])$"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80))
    note: Mapped[str] = mapped_column(String(200), default="")
    line: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3))
    estimated_cents: Mapped[int]
    due_day: Mapped[int]
    recurrence: Mapped[str] = mapped_column(String(20))
    start_month: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 80", name="ck_bills_name_len"),
        CheckConstraint("char_length(note) <= 200", name="ck_bills_note_len"),
        CheckConstraint(f"line IN {tuple(e.value for e in Line)}", name="ck_bills_line"),
        CheckConstraint(f"currency IN {tuple(e.value for e in Currency)}", name="ck_bills_currency"),
        CheckConstraint(
            f"estimated_cents BETWEEN 0 AND {MAX_CENTS}", name="ck_bills_estimated_cents"
        ),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="ck_bills_due_day"),
        CheckConstraint(
            f"recurrence IN {tuple(e.value for e in Recurrence)}", name="ck_bills_recurrence"
        ),
        CheckConstraint(f"start_month ~ '{_MONTH_SQL_RE}'", name="ck_bills_start_month"),
    )


class Payment(Base):
    """At most one payment per bill per period."""

    __tablename__ = "payments"

    bill_id: Mapped[UUID] = mapped_column(
        ForeignKey("bills.id", ondelete="CASCADE"), primary_key=True
    )
    period: Mapped[str] = mapped_column(String(7), primary_key=True)
    actual_cents: Mapped[int]
    paid_at: Mapped[date]

    __table_args__ = (
        CheckConstraint(
            f"actual_cents BETWEEN 0 AND {MAX_CENTS}", name="ck_payments_actual_cents"
        ),
        CheckConstraint(f"period ~ '{_MONTH_SQL_RE}'", name="ck_payments_period"),
        Index("ix_payments_period", "period"),
    )
