# BE-099: Snooze an inbox item

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3 · Milestone M7 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-093, BE-098
- **Can run in parallel with:** BE-100
- **Public endpoint?** no
- **Review size:** ~100 lines, 4 files, ~10 min

## Goal

`POST /inbox/{id}/snooze` hides an item until later today, tomorrow, next week or a chosen date, computed in Mexico City time.

## Why this ticket exists

The epic's snooze options (§5.3) are time rules; each is a small function. Kept separate from the route so the times can be checked by hand.

## Read first

- `api/app/clock.py` (BE-093).

## Design

- **Pattern:** Strategy: a mapping from option to a pure function `(now_local) -> datetime`.

## Packages

None new.

## Details

**Files:** `api/app/inbox/snooze.py` (new), `api/app/inbox/schemas.py` (changed: `SnoozeIn`), `api/app/inbox/router.py` (changed), `api/tests/test_inbox_snooze.py` (new).

```python
class SnoozeOption(StrEnum): LATER_TODAY="later-today"; TOMORROW="tomorrow"; NEXT_WEEK="next-week"; DATE="date"
class SnoozeIn(_CamelModel): option: SnoozeOption; date: date | None = None   # required iff option == "date"
def snooze_until(option: SnoozeOption, now: datetime, tz: ZoneInfo, on: date | None = None) -> datetime   # aware, UTC
```

| Option | Until (local time) |
|---|---|
| `later-today` | now + 3 h |
| `tomorrow` | tomorrow 08:00 |
| `next-week` | next Monday 08:00 (a Monday snoozes 7 days) |
| `date` | that date 08:00; must be after today → else `422` |

Route: `POST /inbox/{id}/snooze` `SnoozeIn` → `200 InboxItemOut` with `status: "snoozed"`, `snoozedUntil` (UTC). Accepted/discarded items → `409`; unknown → `404`; no/wrong credentials → `401`. Items reappear in `GET /inbox` when due (BE-094).

## Steps

1. `snooze_until` + tests.
2. Schema and route + tests.

## Tests

- `test_tomorrow_is_8am_mexico_city`
- `test_next_week_from_monday_is_next_monday`
- `test_later_today_adds_three_hours`
- `test_date_option_requires_future_date_422`
- `test_snoozed_item_hidden_then_back_when_due`
- `test_snooze_requires_credentials`

## Acceptance criteria

- [ ] Times computed in America/Mexico_City, returned in UTC
- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "
from datetime import datetime, timezone; from app.clock import APP_TZ; from app.inbox.snooze import snooze_until
print(snooze_until('tomorrow', datetime(2026,11,22,20,0,tzinfo=timezone.utc), APP_TZ).astimezone(APP_TZ))"
```

Prints `2026-11-23 08:00:00-06:00`. Then snooze an item in `/docs` and see it gone from `GET /inbox`.

## Review guide

1. The option table vs the code mapping.

## Out of scope

- Auto-snooze of stale items in the Weekly reset → EPIC-005.

## Notes / log
