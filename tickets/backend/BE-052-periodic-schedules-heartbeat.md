# BE-052: Periodic schedules table, scheduler process and heartbeat

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-050, BE-051
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 4 files, ~12 min

## Goal

Jobs can be declared to run on a schedule in one table, a scheduler process triggers them, and a heartbeat job proves it every minute.

## Why this ticket exists

Reminders, digests, the weekly reset invite and clean-up are all "run this at these times". One table of schedules means every recurring job in the system is visible in one place, and adding one is a one-line change.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- https://taskiq-python.github.io/guide/scheduling-tasks.html: the scheduler is a separate process that sends tasks at their times; workers still run them.
- Cron syntax: five fields, `minute hour day month weekday`. `*/15 * * * *` is every 15 minutes.

## Design

- **Pattern:** Strategy as a table: schedules are data (`name → cron`), not decorators scattered through the code.
- **Data flow:** `SCHEDULES` → scheduler process → `run_job(name)` at each tick → worker.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/schedules.py` (new).
- `api/app/jobs/broker.py` (changed): the scheduler object, fed from `SCHEDULES`, plus the source needed for one-off delayed jobs from BE-050.
- `Makefile` (changed): `scheduler-dev`. `api/README.md` (changed).
- `api/tests/test_job_schedules.py` (new).

**Table**

```python
class Schedule(BaseModel):          # frozen
    job: str                        # a key of JOBS
    cron: str                       # five-field cron expression
    timezone: str = "America/Mexico_City"

SCHEDULES: tuple[Schedule, ...] = (
    Schedule(job="system.heartbeat", cron="* * * * *"),
)
```

**Heartbeat job.** `system.heartbeat`: `SET jobs:heartbeat <ctx.now ISO> EX 300`. If the key is missing or old, either the scheduler or the worker is down (BE-056 reports it).

**Scheduled job IDs.** Each run is enqueued with `job_id = "<job>:<scheduled minute, UTC>"`, so if two scheduler processes ever run by mistake, each tick still executes once.

**Make**

```make
scheduler-dev: check-db-running ## Start the job scheduler (run exactly one)
```

Only one scheduler process should run. The README says so, and the job ID rule above makes a mistake harmless.

## Steps

1. `Schedule` and `SCHEDULES` with validation tests.
2. Wire the scheduler from the table.
3. The heartbeat job.
4. `make scheduler-dev`.
5. Hand check with worker and scheduler running.

## Tests

- `test_every_schedule_names_a_registered_job`
- `test_every_cron_expression_is_valid`
- `test_every_timezone_exists`
- `test_heartbeat_sets_key_with_ttl`
- `test_scheduled_job_id_includes_the_minute`

## Acceptance criteria

- [ ] All recurring jobs are declared in `SCHEDULES` and nowhere else
- [ ] With worker and scheduler running, `jobs:heartbeat` is refreshed every minute
- [ ] A schedule naming an unknown job fails the test suite
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Three terminals: `make db-up`, `make worker-dev`, `make scheduler-dev`. Then:

```bash
make db-redis-cli
```

`get jobs:heartbeat` shows a time within the last minute. Stop the scheduler and it stops advancing.

## Review guide

Read the diff in this order, and check:

1. `SCHEDULES`: one entry, readable.
2. The job ID rule for scheduled runs.
3. The README note about running one scheduler.

Things that should *not* be in the diff: feature schedules (each feature adds its own line).

## Out of scope

- Delivering Telegram messages every minute → BE-031 adds `telegram.deliver_due`.
- Daily clean-up → BE-055.

## Notes / log

The agent adds progress notes, decisions and open questions here.
