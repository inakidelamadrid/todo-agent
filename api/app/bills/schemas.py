"""API schemas for bills and payments.

Frozen Pydantic models, snake_case internally, camelCase on the wire
(matching `web/src/features/bills/model/types.ts`).
"""

import re
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.bills.domain import parse_month

MAX_CENTS = 1_000_000_000


class Line(StrEnum):
    UTILITIES = "utilities"
    TELECOM = "telecom"
    STREAMING = "streaming"
    SOFTWARE = "software"


class Currency(StrEnum):
    MXN = "MXN"
    USD = "USD"


class Recurrence(StrEnum):
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    YEARLY = "yearly"


def _valid_month(value: str) -> str:
    parse_month(value)  # raises ValueError on bad input -> 422
    return value


Month = Annotated[str, AfterValidator(_valid_month)]


def _strip(value: str) -> str:
    return value.strip()


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
    )


class _BillBase(_CamelModel):
    name: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=80)]
    note: Annotated[str, Field(max_length=200)] = ""
    line: Line
    currency: Currency
    estimated_cents: Annotated[int, Field(ge=0, le=MAX_CENTS)]
    due_day: Annotated[int, Field(ge=1, le=31)]
    recurrence: Recurrence
    start_month: Month


class BillCreate(_BillBase):
    pass


class BillUpdate(_CamelModel):
    """All fields optional; same validation when present."""

    name: Annotated[str, AfterValidator(_strip), Field(min_length=1, max_length=80)] | None = None
    note: Annotated[str, Field(max_length=200)] | None = None
    line: Line | None = None
    currency: Currency | None = None
    estimated_cents: Annotated[int, Field(ge=0, le=MAX_CENTS)] | None = None
    due_day: Annotated[int, Field(ge=1, le=31)] | None = None
    recurrence: Recurrence | None = None
    start_month: Month | None = None


class BillOut(_BillBase):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    id: UUID
    created_at: datetime
    updated_at: datetime


class PaymentIn(_CamelModel):
    actual_cents: Annotated[int, Field(ge=0, le=MAX_CENTS)]
    paid_at: date


class PaymentOut(PaymentIn):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        frozen=True,
        from_attributes=True,
    )

    bill_id: UUID
    period: str
