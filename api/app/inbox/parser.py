"""DumpParser port for the inbox.

A parser turns raw text and today's date into a strict ``ParseDumpResult``.
Adapters live in ``app/inbox/parsers/``; the inbox code only depends on
this port.
"""

from collections.abc import Awaitable, Callable
from datetime import date

from app.inbox.schemas import ParseDumpResult

DumpParser = Callable[[str, date], Awaitable[ParseDumpResult]]


async def unconfigured_parser(raw_text: str, today: date) -> ParseDumpResult:
    """Default adapter: refuses to parse, forcing a fallback item."""
    raise RuntimeError("No dump parser is configured")
