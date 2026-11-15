# BE-055: Daily clean-up job

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-052, BE-054, BE-011
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~40 lines, 3 files, ~6 min

## Goal

Once a day, Telegram update records and job failure records older than 30 days are deleted.

## Why this ticket exists

Both tables grow forever otherwise. It is also the first real scheduled job, showing how little a feature needs to add: one function, one registry entry, one schedule line.

## Read first

- `delete_updates_before` (BE-011), `delete_failures_before` (BE-054).
- `api/app/jobs/schedules.py`.

## Design

- **Pattern:** Thin job: compute the cutoff, call two repository functions.
- **Data flow:** 03:30 daily → `system.cleanup` → cutoff = `ctx.now - 30 days` → two deletes → log counts.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/system_jobs.py` (new): `async def cleanup(ctx, payload) -> None`.
- `api/app/jobs/queue.py` (changed): register `system.cleanup`. `api/app/jobs/schedules.py` (changed): `Schedule(job="system.cleanup", cron="30 3 * * *")`.
- `api/tests/test_cleanup_job.py` (new).

- `RETENTION_DAYS = 30`, a named constant.
- Logs `job.cleanup` with the two deleted counts.
- Safe to run twice in a day (the second run deletes nothing).

## Steps

1. The job function.
2. Registry entry and schedule line.
3. Tests.

## Tests

- `test_cleanup_deletes_rows_older_than_30_days_only`
- `test_cleanup_twice_is_harmless`
- `test_cleanup_is_scheduled_daily`

## Acceptance criteria

- [ ] Rows older than 30 days are removed from both tables; newer rows stay
- [ ] The job is declared in `SCHEDULES`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The cutoff calculation uses `ctx.now`.
2. Three small edits, no other files.

Things that should *not* be in the diff: cleaning the Telegram outbox (sent messages are kept until a retention decision is made).

## Out of scope

- Outbox retention → decide when BE-031 is in use.

## Assumptions

- 30 days retention for both tables (my recommendation; you did not answer this one).

## Notes / log

The agent adds progress notes, decisions and open questions here.
