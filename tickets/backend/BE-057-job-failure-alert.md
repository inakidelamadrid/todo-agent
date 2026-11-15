# BE-057: Tell the owner when a job fails for good

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-054, BE-030, BE-031
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 3 files, ~10 min

## Goal

When a job gives up, you get one calm Telegram message naming the job, at most once per job name per hour.

## Why this ticket exists

A status page only helps if you look at it. This closes the loop for the case that matters: something you were counting on did not happen.

## Read first

- `api/app/telegram/service.py`: `send` and its idempotency key.
- `on_job_failed` in `api/app/jobs/broker.py`.

## Design

- **Pattern:** Thin function over the Telegram service; deduplication through the idempotency key, not extra state.
- **Data flow:** `on_job_failed` → `alert_job_failed(session, job, now)` → `service.send(category="system", idempotency_key="system:job-failed:<job>:<YYYY-MM-DDTHH>")`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/alerts.py` (new).
- `api/app/telegram/templates.py` (changed): `job_failed` = `A background job didn't finish: <code>{job}</code>. Nothing else is affected.`
- `api/app/jobs/broker.py` (changed): the hook calls it after `record_failure`.
- `api/tests/test_job_alerts.py` (new).

**Rules**

- The idempotency key includes the job name and the hour, so repeated failures of one job produce one message per hour.
- Goes through `service.send`, so quiet hours, pause and caps apply: a failure at 02:00 is reported at 08:00.
- **No alert for Telegram's own jobs** (`telegram.*`): if delivery is what failed, sending a message about it cannot work. Those are visible in `GET /jobs/status` and the Telegram status card only.
- The recipient is `settings.telegram_allowed_user_id`; unset → no alert, no error.
- The message contains the job name only: no IDs, payloads or error text.
- A failure inside the alert is logged (`job.alert_failed`) and swallowed; it must never crash the worker or trigger another alert.

## Steps

1. `alert_job_failed`.
2. Template.
3. Call it from the hook.
4. Tests.

## Tests

- `test_failure_enqueues_one_alert`
- `test_second_failure_same_hour_does_not_add_a_message`
- `test_failure_next_hour_adds_a_message`
- `test_telegram_job_failure_sends_no_alert`
- `test_no_owner_configured_sends_nothing`
- `test_alert_error_is_swallowed`

## Acceptance criteria

- [ ] At most one alert per job name per hour
- [ ] Alerts respect quiet hours and pause
- [ ] No alert is attempted for `telegram.*` jobs
- [ ] The message has no payload or error detail
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

By hand: register a test job that raises `NoRetry`, enqueue it during the day: one message arrives.

## Review guide

Read the diff in this order, and check:

1. The idempotency key.
2. The `telegram.*` exclusion.
3. The swallow-and-log around the alert.

Things that should *not* be in the diff: email alerts (EPIC-007).

## Out of scope

- Email as the fallback alert channel → EPIC-007 / BE-034.

## Assumptions

- Alert by Telegram, one per job per hour, log only when Telegram is what failed (my recommendation; you did not answer this one).

## Notes / log

The agent adds progress notes, decisions and open questions here.
