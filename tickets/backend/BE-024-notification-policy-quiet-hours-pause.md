# BE-024: Notification policy: quiet hours and pause

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3 Central policies, §6
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-004 to BE-023
- **Public endpoint?** no
- **Review size:** ~100 lines, 3 files, ~15 min

## Goal

A pure function decides, for a message category at a given moment, whether to send now or defer, based on quiet hours and pause.

## Why this ticket exists

The epic wants these rules enforced centrally for every channel (Telegram now, email in EPIC-007). They are pure date arithmetic with tricky edges (a window that crosses midnight, time zones), which is exactly what should be isolated and tested exhaustively before any queue exists.

## Read first

- `api/app/bills/domain.py`: pure rules with the date passed in.
- `zoneinfo` in the standard library (IANA time zones; no extra package).
- `Epics/README.md` conventions: default time zone America/Mexico_City; quiet hours respected everywhere.

## Design

- **Pattern:** Pure decision function returning a tagged union (`SendNow | Defer`). The clock is an argument, never read inside.
- **Data flow:** `(category, policy, now)` → `decide_time` → `SendNow()` or `Defer(until)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files** (a new package, because email will share it)

- `api/app/notifications/__init__.py` (new, empty).
- `api/app/notifications/policy.py` (new).
- `api/tests/test_notification_policy.py` (new).

**Types (frozen)**

```python
class NotificationPolicy(BaseModel):
    quiet_start: time = time(20, 0)
    quiet_end: time = time(8, 0)
    timezone: str = "America/Mexico_City"
    paused_until: datetime | None = None          # aware, UTC
    urgent_categories: frozenset[str] = frozenset()

class SendNow(BaseModel):
    kind: Literal["send_now"] = "send_now"

class Defer(BaseModel):
    kind: Literal["defer"] = "defer"
    until: datetime                                # aware, UTC

Decision = SendNow | Defer
```

**Functions (pure)**

- `in_quiet_hours(local: time, start: time, end: time) -> bool`: start inclusive, end exclusive. Handles windows crossing midnight (20:00–08:00) and same-day windows (13:00–15:00). `start == end` means no quiet hours.
- `quiet_end_after(now: datetime, policy) -> datetime`: the next moment quiet hours end, in UTC.
- `decide_time(category: str, policy: NotificationPolicy, now: datetime) -> Decision`
  1. `category in policy.urgent_categories` → `SendNow` (urgent bypasses both pause and quiet hours, epic §5.3).
  2. `paused_until` is set and `now < paused_until` → `Defer(paused_until)`.
  3. In quiet hours → `Defer(quiet_end_after(now, policy))`.
  4. Otherwise `SendNow`.
- `now` must be timezone-aware; a naive datetime raises `ValueError`.

Messages are deferred, never dropped.

## Steps

1. Types.
2. `in_quiet_hours` with a table of cases.
3. `quiet_end_after`.
4. `decide_time`.

## Tests

- `test_in_quiet_hours_crossing_midnight` (parametrised: 19:59 no, 20:00 yes, 23:59 yes, 00:00 yes, 07:59 yes, 08:00 no).
- `test_in_quiet_hours_same_day_window`
- `test_equal_start_and_end_means_never_quiet`
- `test_evening_message_defers_to_next_morning_local_time`
- `test_early_morning_message_defers_to_same_morning`
- `test_daytime_message_sends_now`
- `test_pause_defers_until_paused_until`
- `test_expired_pause_is_ignored`
- `test_urgent_category_bypasses_pause_and_quiet_hours`
- `test_naive_now_raises`
- `test_defer_time_is_correct_across_a_dst_change`: use a zone that has DST, e.g. `America/New_York`.

## Acceptance criteria

- [ ] Default quiet hours are 20:00–08:00 America/Mexico_City
- [ ] No function reads the system clock or the database
- [ ] A deferred message's `until` is always in the future and timezone-aware
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `in_quiet_hours`: walk the six boundary cases by hand.
2. `decide_time`: the order of the four rules.
3. No `datetime.now()` anywhere in the module.

Things that should *not* be in the diff: caps, grouping, database, Telegram imports.

## Out of scope

- Caps and grouping → BE-025.
- Storing the policy → BE-026.
- Applying it to real messages → BE-030.

## Assumptions

- Quiet hours 20:00–08:00, as answered (question 5).
- You did not say which categories may break through. Default: none (`urgent_categories` is empty). The setting exists, so it is one PATCH away (BE-027).

## Notes / log

The agent adds progress notes, decisions and open questions here.
