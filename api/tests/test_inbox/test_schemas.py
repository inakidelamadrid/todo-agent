"""Tests for inbox schemas (BE-089)."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.inbox.schemas import (
    Confidence,
    DumpIn,
    DumpSource,
    Energy,
    ExpenseCandidate,
    ItemType,
    NoteCandidate,
    ParseDumpResult,
    ReminderCandidate,
    TaskCandidate,
    TaskContext,
    TaskSize,
)


def test_dump_in_trims_and_requires_raw_text():
    dump = DumpIn(raw_text="  Call dentist  ")
    assert dump.raw_text == "Call dentist"
    assert dump.source == DumpSource.WEB


def test_dump_in_rejects_empty_raw_text():
    with pytest.raises(ValidationError):
        DumpIn(raw_text="   ")


def test_task_candidate_defaults():
    item = TaskCandidate(type=ItemType.TASK, summary="Call dentist")
    assert item.size == TaskSize.S
    assert item.energy == Energy.MEDIUM
    assert item.context == TaskContext.ANYWHERE
    assert item.confidence == Confidence.MEDIUM
    assert item.first_step == ""


def test_expense_candidate_requires_amount_and_currency():
    item = ExpenseCandidate(
        type=ItemType.EXPENSE,
        summary="Gym",
        amount_cents=60000,
        currency="MXN",
    )
    assert item.amount_cents == 60000

    with pytest.raises(ValidationError):
        ExpenseCandidate(type=ItemType.EXPENSE, summary="Gym", amount_cents=-1, currency="MXN")


def test_parse_result_rejects_empty_items():
    with pytest.raises(ValidationError):
        ParseDumpResult(items=())


def test_parse_result_accepts_discriminated_union():
    result = ParseDumpResult(
        items=(
            TaskCandidate(type=ItemType.TASK, summary="Call dentist"),
            ReminderCandidate(type=ItemType.REMINDER, summary="Dentist", do_date=date.today()),
            NoteCandidate(type=ItemType.NOTE, summary="Note", body="Body"),
            ExpenseCandidate(
                type=ItemType.EXPENSE,
                summary="Gym",
                amount_cents=60000,
                currency="MXN",
            ),
        )
    )
    assert len(result.items) == 4


def test_task_payload_with_amount_cents_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        TaskCandidate(type="task", summary="x", amountCents=100)
    assert "amountCents" in str(exc_info.value) or "Extra inputs are not permitted" in str(exc_info.value)
