"""Unit tests for schema validation edges (no database)."""

import pytest
from pydantic import ValidationError

from app.bills.schemas import BillCreate, BillUpdate

VALID = {
    "name": "Electricity",
    "line": "utilities",
    "currency": "MXN",
    "estimatedCents": 150_000,
    "dueDay": 15,
    "recurrence": "monthly",
    "startMonth": "2026-01",
}


def _create(**overrides):
    data = {**VALID, **overrides}
    return BillCreate.model_validate(data)


def test_valid_camel_case_payload_accepted() -> None:
    bill = _create()
    assert bill.estimated_cents == 150_000
    assert bill.due_day == 15


def test_snake_case_also_accepted() -> None:
    bill = BillCreate(
        name="Water",
        line="utilities",
        currency="USD",
        estimated_cents=900,
        due_day=3,
        recurrence="monthly",
        start_month="2026-02",
    )
    assert bill.name == "Water"


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_name_blank_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        _create(name=name)


def test_name_trimmed() -> None:
    assert _create(name="  Gas  ").name == "Gas"


def test_name_too_long_rejected() -> None:
    with pytest.raises(ValidationError):
        _create(name="x" * 81)
    assert _create(name="x" * 80).name == "x" * 80


def test_note_length_limit() -> None:
    assert _create(note="n" * 200).note == "n" * 200
    with pytest.raises(ValidationError):
        _create(note="n" * 201)


@pytest.mark.parametrize("due_day", [0, 32, -1])
def test_due_day_out_of_range_rejected(due_day: int) -> None:
    with pytest.raises(ValidationError):
        _create(dueDay=due_day)


@pytest.mark.parametrize("cents", [-1, 1_000_000_001])
def test_cents_out_of_range_rejected(cents: int) -> None:
    with pytest.raises(ValidationError):
        _create(estimatedCents=cents)


@pytest.mark.parametrize("cents", [0, 1_000_000_000])
def test_cents_bounds_accepted(cents: int) -> None:
    assert _create(estimatedCents=cents).estimated_cents == cents


@pytest.mark.parametrize("month", ["2026-13", "not-a-month", "2026-1"])
def test_start_month_invalid_rejected(month: str) -> None:
    with pytest.raises(ValidationError):
        _create(startMonth=month)


def test_bad_enum_rejected() -> None:
    with pytest.raises(ValidationError):
        _create(line="insurance")
    with pytest.raises(ValidationError):
        _create(currency="EUR")
    with pytest.raises(ValidationError):
        _create(recurrence="weekly")


def test_update_is_frozen_and_partial() -> None:
    patch = BillUpdate.model_validate({"dueDay": 20})
    assert patch.model_dump(exclude_unset=True) == {"due_day": 20}
    with pytest.raises(ValidationError):
        patch.due_day = 21
    with pytest.raises(ValidationError):
        BillUpdate.model_validate({"name": " "})
