# BE-031: Deliver due outbound messages

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3
- **Assigned agent / harness / model:**
- **Depends on:** BE-019, BE-030, BE-051, BE-052
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~120 lines, 3 files, ~15 min

## Goal

A job run by the scheduler sends every outbox row whose time has come and records the result.

## Why this ticket exists

It closes the outbound loop. The delivery logic is a plain function; a thin job wraps it and one line in the schedules table (BE-052) runs it every minute.

## Read first

- `api/app/jobs/queue.py` (`JobContext`, `JOBS`) and `api/app/jobs/schedules.py` (BE-047, BE-051, BE-052).
- `api/app/telegram/service.py`, `repository.py`, `sender.py`.
- `api/app/notifications/policy.py`: `should_group`, `merge_texts`.

## Design

- **Pattern:** Outbox worker: a plain async function `deliver_due(...)`; the scheduler is only its caller.
- **Data flow:** `SCHEDULES` (every minute) → `telegram.deliver_due` job → `deliver_due(session, sender, secret, now)` → `due_messages` → group → render → `sender.send` → `mark_sent` / `mark_attempt`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `taskiq` | installed (BE-048) | Runs the job | Reached only through our `JOBS` registry and `SCHEDULES` table; this ticket imports no taskiq. |

## Details

**Files**

- `api/app/telegram/repository.py` (changed): `due_messages(session, now, limit=20)` using `FOR UPDATE SKIP LOCKED`; `mark_sent(session, id, telegram_message_id, now)`; `mark_attempt(session, id, status, scheduled_for)`.
- `api/app/telegram/delivery.py` (new): `async def deliver_due(session, sender, secret, now, limit=20) -> DeliveryReport` (frozen: `sent`, `deferred`, `failed`).
- `api/tests/test_telegram_delivery.py` (new).

**Behaviour**

- Rows with status `queued` or `deferred` and `scheduled_for <= now`, oldest first.
- Re-check the policy for each row with `decide(...)`: if it now says `Defer` (you paused since it was queued), update `scheduled_for` and skip.
- Rows for the same chat and category whose `scheduled_for` fall within the grouping window are merged with `merge_texts` into one message; all of them are marked sent with the same message ID.
- `SendFailed` → `attempts + 1`; after 5 attempts → `failed`.
- `FOR UPDATE SKIP LOCKED` lets two workers run without sending the same row twice.

**Registration.** `api/app/telegram/jobs.py` (new): `async def deliver_due_job(ctx, payload)` calls `deliver_due(ctx.session, ctx.sender, secret, ctx.now)`. Register it in `JOBS` as `telegram.deliver_due` and add `Schedule(job="telegram.deliver_due", cron="* * * * *")` to `SCHEDULES`.

## Steps

1. Repository functions.
2. `deliver_due` without grouping.
3. Add the policy re-check.
4. Add grouping.
5. Add the job wrapper, the `JOBS` entry and the `SCHEDULES` line.

## Tests

- `test_due_row_is_sent_and_marked`
- `test_future_row_is_left_alone`
- `test_row_is_redeferred_when_paused_meanwhile`
- `test_rows_in_window_merge_into_one_message`
- `test_failure_increments_attempts`
- `test_fifth_failure_marks_failed`
- `test_two_concurrent_runs_send_each_row_once`
- `test_deliver_due_is_scheduled_every_minute`

## Acceptance criteria

- [ ] Each row is sent at most once, including with two concurrent runs
- [ ] Policy changes made after queueing are respected
- [ ] The function works with the recording fake and needs no scheduler to test
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

By hand: queue a message with `service.send` from a shell during the day; it arrives on the next tick.

## Review guide

Read the diff in this order, and check:

1. `due_messages`: the locking clause.
2. `deliver_due`: where a row's status changes, and that it changes exactly once per run.

Things that should *not* be in the diff: honouring 429 (BE-032); any taskiq import.

## Out of scope

- 429 and backoff → BE-032.
- Email fallback → BE-034.

## Notes / log

The agent adds progress notes, decisions and open questions here.
