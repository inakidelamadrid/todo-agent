# BE-032: Honour Telegram 429 retry_after and back off

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3 Telegram rate limits, Failure handling
- **Assigned agent / harness / model:**
- **Depends on:** BE-031
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files, ~10 min

## Goal

When Telegram answers 429, the message is rescheduled for exactly when Telegram says; other failures back off exponentially.

## Why this ticket exists

Telegram throttles bots and tells them how long to wait. Ignoring it gets the bot limited harder. Because our retries are rows with a `scheduled_for`, backing off is a date calculation, not a sleeping loop.

## Read first

- `RateLimited` in `api/app/telegram/sender.py`.
- https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this

## Design

- **Pattern:** Retry with backoff expressed as data: a pure function computes the next attempt time.
- **Data flow:** `RateLimited(retry_after)` → `next_attempt_at(...)` → `mark_attempt(scheduled_for=…)`.

## Packages

None new. Standard library and what is already installed.

Hand-written instead of a package: `next_attempt_at`, about 10 lines. `tenacity` (9.2.1, Apache-2.0) was considered: it retries by sleeping inside the process, which would hold a worker and lose the retry on restart. Our retry state already lives in the outbox row.

## Details

**Files**

- `api/app/telegram/delivery.py` (changed).
- `api/tests/test_telegram_delivery.py` (changed).

**Pure function**

```python
MAX_ATTEMPTS = 5

def next_attempt_at(now: datetime, attempts: int, retry_after: float | None) -> datetime
```
- `retry_after` given → `now + retry_after + 1 s`.
- Otherwise `now + min(30 s * 2**attempts, 15 min)`.

**Delivery**

- `RateLimited` → reschedule with `retry_after`; **does not** count as an attempt (Telegram asked us to wait; nothing is wrong with the message). Stop the current run: later rows would hit the same limit.
- Other `SendFailed` → attempts + 1, reschedule with backoff; at `MAX_ATTEMPTS` → `failed`.

## Steps

1. `next_attempt_at` with tests.
2. Use it in both failure branches.
3. Stop the run on `RateLimited`.

## Tests

- `test_retry_after_is_honoured_plus_margin`
- `test_backoff_doubles_and_is_capped`
- `test_rate_limited_does_not_consume_an_attempt`
- `test_run_stops_after_rate_limit`
- `test_message_fails_after_max_attempts`

## Acceptance criteria

- [ ] A 429 never causes an immediate retry
- [ ] No `sleep` is used for retries
- [ ] A rate limit leaves `attempts` unchanged
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `next_attempt_at`: the two formulas.
2. The two failure branches in `deliver_due`.

Things that should *not* be in the diff: a new dependency; email fallback.

## Out of scope

- Falling back to email after long outages → BE-034.

## Notes / log

The agent adds progress notes, decisions and open questions here.
