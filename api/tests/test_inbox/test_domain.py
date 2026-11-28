"""Tests for inbox domain helpers."""

from datetime import UTC, date
from uuid import uuid4

from app.inbox.domain import drafts_from_result, fallback_result, today_in
from app.inbox.models import InboxItem
from app.inbox.schemas import (
    Confidence,
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


def test_today_in_respects_timezone():
    from datetime import datetime

    utc_3am = datetime(2026, 11, 28, 3, 0, 0, tzinfo=UTC)
    assert today_in("America/Mexico_City", utc_3am) == date(2026, 11, 27)


def test_fallback_result_is_low_confidence_task():
    result = fallback_result("call dentist, buy cat food")
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, TaskCandidate)
    assert item.summary == "call dentist, buy cat food"
    assert item.confidence == Confidence.LOW


def test_drafts_from_result_task_includes_triage_data():
    dump_id = uuid4()
    result = ParseDumpResult(
        items=(
            TaskCandidate(
                type=ItemType.TASK,
                summary="Call dentist",
                size=TaskSize.S,
                energy=Energy.LOW,
                context=TaskContext.PHONE,
                do_date=date(2026, 12, 1),
                first_step="Find the number",
                confidence=Confidence.HIGH,
            ),
        )
    )
    drafts = drafts_from_result(dump_id, result)
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft["dump_id"] == dump_id
    assert draft["type"] == "task"
    assert draft["summary"] == "Call dentist"
    assert draft["size"] == "S"
    assert draft["energy"] == "low"
    assert draft["context"] == "phone"
    assert draft["do_date"] == date(2026, 12, 1)
    assert draft["due_date"] is None
    assert draft["first_step"] == "Find the number"
    assert draft["confidence"] == "high"


def test_drafts_from_result_reminder_note_expense():
    dump_id = uuid4()
    result = ParseDumpResult(
        items=(
            ReminderCandidate(
                type=ItemType.REMINDER,
                summary="Dentist appointment",
                do_date=date(2026, 12, 5),
            ),
            NoteCandidate(
                type=ItemType.NOTE,
                summary="Idea",
                body="Buy a better toothbrush",
            ),
            ExpenseCandidate(
                type=ItemType.EXPENSE,
                summary="Gym membership",
                amount_cents=60000,
                currency="MXN",
            ),
        )
    )
    drafts = drafts_from_result(dump_id, result)
    assert len(drafts) == 3

    reminder, note, expense = drafts
    assert reminder["do_date"] == date(2026, 12, 5)
    assert note["body"] == "Buy a better toothbrush"
    assert expense["amount_cents"] == 60000
    assert expense["currency"] == "MXN"


def test_every_draft_key_is_an_inbox_item_column():
    """Regression: drafts_from_result must only emit keys that InboxItem can consume."""
    dump_id = uuid4()
    result = ParseDumpResult(
        items=(
            TaskCandidate(
                type=ItemType.TASK,
                summary="Task",
                size=TaskSize.M,
                energy=Energy.MEDIUM,
                context=TaskContext.COMPUTER,
                do_date=date(2026, 12, 1),
                due_date=date(2026, 12, 2),
                first_step="Open laptop",
            ),
            ReminderCandidate(
                type=ItemType.REMINDER,
                summary="Reminder",
                do_date=date(2026, 12, 3),
            ),
            NoteCandidate(
                type=ItemType.NOTE,
                summary="Note",
                body="Body",
            ),
            ExpenseCandidate(
                type=ItemType.EXPENSE,
                summary="Expense",
                amount_cents=100,
                currency="USD",
            ),
        )
    )
    drafts = drafts_from_result(dump_id, result)
    allowed = set(InboxItem.__table__.columns.keys())
    for draft in drafts:
        for key in draft:
            assert key in allowed, f"draft key {key!r} is not an InboxItem column"
