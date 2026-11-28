"""Fake parser adapter for tests."""

from datetime import date

from app.inbox.parser import DumpParser
from app.inbox.schemas import (
    NoteCandidate,
    ParseDumpResult,
    TaskCandidate,
)


def fake_parser(*items: TaskCandidate | NoteCandidate) -> DumpParser:
    """Return a parser that ignores input and yields the canned items."""
    result = ParseDumpResult(items=items)

    async def _parse(raw_text: str, today: date) -> ParseDumpResult:
        return result

    return _parse
