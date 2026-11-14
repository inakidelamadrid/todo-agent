"""Pure domain logic for bills: month math and the due rule.

No I/O, no FastAPI, no SQLAlchemy — mirrors
`web/src/features/bills/model/schedule.ts`.
"""

import re

# Recurrence -> step in months. Mirrors the frontend's STEP.
RECURRENCE_STEP: dict[str, int] = {"monthly": 1, "bimonthly": 2, "yearly": 12}

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
MONTH_PATTERN = _MONTH_RE.pattern


def parse_month(value: str) -> tuple[int, int]:
    """Validate a `YYYY-MM` month key, returning (year, month)."""
    match = _MONTH_RE.match(value)
    if not match:
        raise ValueError(f"Invalid month {value!r}: expected YYYY-MM, month 01-12")
    return int(match.group(1)), int(match.group(2))


def month_index(month: str) -> int:
    """Absolute month number, so month differences cross year boundaries."""
    year, mon = parse_month(month)
    return year * 12 + (mon - 1)


def is_due_in_month(recurrence: str, start_month: str, month: str) -> bool:
    """A bill is due in `month` when month >= startMonth and the difference
    in months is divisible by the recurrence step (1, 2 or 12)."""
    diff = month_index(month) - month_index(start_month)
    return diff >= 0 and diff % RECURRENCE_STEP[recurrence] == 0
