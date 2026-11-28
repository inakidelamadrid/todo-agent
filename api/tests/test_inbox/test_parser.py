"""Tests for the DumpParser port and fake adapter (BE-090)."""

import asyncio
from datetime import date

import pytest

from app.inbox.parser import unconfigured_parser
from app.inbox.parsers.fake import fake_parser
from app.inbox.schemas import (
    ItemType,
    NoteCandidate,
    ParseDumpResult,
    TaskCandidate,
)


def test_fake_parser_returns_canned_items():
    parser = fake_parser(
        TaskCandidate(type=ItemType.TASK, summary="One"),
        NoteCandidate(type=ItemType.NOTE, summary="Two", body="note body"),
    )
    result = asyncio.run(parser("x", date.today()))
    assert isinstance(result, ParseDumpResult)
    assert len(result.items) == 2
    assert result.items[0].summary == "One"
    assert result.items[1].summary == "Two"


def test_unconfigured_parser_raises():
    with pytest.raises(RuntimeError):
        asyncio.run(unconfigured_parser("x", date.today()))
