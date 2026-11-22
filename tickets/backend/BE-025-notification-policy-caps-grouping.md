# BE-025: Notification policy: per-category caps and grouping

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-024
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~110 lines, 2 files, ~15 min

## Goal

The policy also limits how many messages a category may send per day and decides when nearby messages should merge into one.

## Why this ticket exists

Reminder fatigue is the main risk the radar and reset epics name. Caps and grouping are the mitigations, and like quiet hours they are pure rules. They are separate from BE-024 because they need a second input (what was already sent).

## Read first

- `api/app/notifications/policy.py` from BE-024.

## Design

- **Pattern:** Pure decision function composed from smaller ones.
- **Data flow:** `(category, policy, now, sent_today)` → `decide` → `decide_time` then `apply_cap` → `Decision`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/notifications/policy.py` (changed).
- `api/tests/test_notification_policy.py` (changed).

**Policy fields added**

- `caps: Mapping[str, int] = {}`: category → maximum messages per local day. A missing category is uncapped. `0` silences a category (still deferred to the next day, never dropped silently: see below).
- `grouping_window_minutes: int = 5` (0–120; 0 disables grouping).

**Functions (pure)**

- `local_day_start(now: datetime, policy) -> datetime`: midnight today in the policy's zone, as UTC. The queue uses it to count "sent today".
- `next_send_window(now, policy) -> datetime`: the first moment tomorrow that is outside quiet hours.
- `apply_cap(category, policy, now, sent_today: int) -> Decision`: urgent → `SendNow`; `sent_today >= cap` → `Defer(next_send_window(...))`; else `SendNow`.
- `decide(category, policy, now, sent_today) -> Decision`: `decide_time` first; if that is `SendNow`, then `apply_cap`.
- `should_group(first_scheduled: datetime, candidate_scheduled: datetime, window_minutes: int) -> bool`: true when both fall within the window.
- `merge_texts(texts: Sequence[str]) -> str`: joins rendered messages with a blank line; raises `ValueError` over 4096 characters (the caller then sends separately).

A cap of `0` defers forever in practice. That is intentional and visible in the status endpoint (BE-043) as a growing deferred count, rather than messages vanishing.

## Steps

1. Add the fields.
2. `local_day_start`, `next_send_window`.
3. `apply_cap`, then `decide`.
4. `should_group`, `merge_texts`.

## Tests

- `test_uncapped_category_sends`
- `test_cap_reached_defers_to_next_send_window`
- `test_next_send_window_is_after_quiet_hours`
- `test_urgent_ignores_cap`
- `test_decide_checks_time_before_cap`
- `test_local_day_start_uses_policy_timezone`
- `test_should_group_inside_and_outside_window`
- `test_zero_window_never_groups`
- `test_merge_texts_joins_with_blank_line`
- `test_merge_texts_refuses_over_4096`

## Acceptance criteria

- [ ] `decide` is the single entry point later tickets call
- [ ] A capped message is deferred to a time outside quiet hours
- [ ] All functions remain pure
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `decide`: time rules first, cap second.
2. `next_send_window`: could it ever return a time inside quiet hours?

Things that should *not* be in the diff: database counting (the caller supplies `sent_today`); sending.

## Out of scope

- Counting sent messages → BE-029.
- Calling `decide` → BE-030.
- Merging queued rows → BE-031.

## Assumptions

- Grouping window 5 minutes; no caps by default. EPIC-004 will set `radar: 1` when it lands.

## Notes / log

The agent adds progress notes, decisions and open questions here.
