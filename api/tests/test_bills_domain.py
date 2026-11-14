"""Unit tests for the pure due rule and month math."""

import pytest

from app.bills.domain import RECURRENCE_STEP, is_due_in_month, month_index, parse_month

MONTHLY_BILL = ("monthly", "2025-01")
BIMONTHLY_BILL = ("bimonthly", "2025-01")
YEARLY_BILL = ("yearly", "2025-03")


@pytest.mark.parametrize(
    ("recurrence", "start", "month", "expected"),
    [
        # monthly: due every month from startMonth on
        ("monthly", "2025-01", "2025-01", True),
        ("monthly", "2025-01", "2025-07", True),
        ("monthly", "2025-01", "2024-12", False),  # before start
        # bimonthly: every second month
        ("bimonthly", "2025-01", "2025-01", True),
        ("bimonthly", "2025-01", "2025-02", False),
        ("bimonthly", "2025-01", "2025-03", True),
        ("bimonthly", "2025-01", "2026-01", True),  # across year boundary
        ("bimonthly", "2025-01", "2026-02", False),
        ("bimonthly", "2025-11", "2026-01", True),  # Nov -> Jan wraps cleanly
        ("bimonthly", "2025-11", "2025-12", False),
        # yearly: same month each year
        ("yearly", "2025-03", "2025-03", True),
        ("yearly", "2025-03", "2026-03", True),
        ("yearly", "2025-03", "2025-04", False),
        ("yearly", "2025-03", "2025-02", False),
    ],
)
def test_is_due_in_month(recurrence: str, start: str, month: str, expected: bool) -> None:
    assert is_due_in_month(recurrence, start, month) is expected


def test_recurrence_step_matches_frontend() -> None:
    # Mirrors STEP in web/src/features/bills/model/schedule.ts
    assert RECURRENCE_STEP == {"monthly": 1, "bimonthly": 2, "yearly": 12}


def test_month_index_crosses_years() -> None:
    assert month_index("2026-01") - month_index("2025-12") == 1
    assert month_index("2026-01") == month_index("2025-01") + 12


@pytest.mark.parametrize(
    "bad",
    ["", "2025-00", "2025-13", "2025-1", "25-01", "2025/01", "2025-1x", "abcd-ef"],
)
def test_parse_month_rejects_invalid(bad: str) -> None:
    with pytest.raises(ValueError, match="YYYY-MM"):
        parse_month(bad)


def test_parse_month_accepts_valid() -> None:
    assert parse_month("2025-01") == (2025, 1)
    assert parse_month("1999-12") == (1999, 12)
