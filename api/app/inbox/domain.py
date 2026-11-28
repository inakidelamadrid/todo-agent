"""Pure domain logic for the inbox.

Mapping from parser results to item drafts, and date helpers. No I/O.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.inbox.schemas import (
    Confidence,
    ExpenseCandidate,
    ItemType,
    NoteCandidate,
    ParseDumpResult,
    ReminderCandidate,
    TaskCandidate,
)


def today_in(tz: str, now: datetime) -> date:
    """Calendar date in the given timezone for a UTC-aware moment."""
    return now.astimezone(ZoneInfo(tz)).date()


def fallback_result(raw_text: str) -> ParseDumpResult:
    """A single low-confidence task holding the raw text.

    Used when no parser is configured or parsing fails.
    """
    return ParseDumpResult(
        items=(
            TaskCandidate(
                type=ItemType.TASK,
                summary=raw_text,
                confidence=Confidence.LOW,
            ),
        )
    )


def drafts_from_result(
    dump_id,
    result: ParseDumpResult,
) -> list[dict]:
    """Turn a parse result into inbox item dicts ready for the repository."""
    rows: list[dict] = []
    for item in result.items:
        row: dict = {
            "dump_id": dump_id,
            "type": item.type.value,
            "status": "new",
            "summary": item.summary,
            "confidence": item.confidence.value,
        }
        match item:
            case TaskCandidate():
                row.update(
                    {
                        "size": item.size.value,
                        "energy": item.energy.value,
                        "context": item.context.value,
                        "do_date": item.do_date,
                        "due_date": item.due_date,
                        "first_step": item.first_step,
                    }
                )
            case ReminderCandidate():
                row.update({"do_date": item.do_date})
            case NoteCandidate():
                row.update({"body": item.body})
            case ExpenseCandidate():
                row.update(
                    {
                        "amount_cents": item.amount_cents,
                        "currency": item.currency,
                    }
                )
        rows.append(row)
    return rows
