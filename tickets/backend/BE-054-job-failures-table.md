# BE-054: Record jobs that failed for good

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-053
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 4 files + generated migration, ~12 min

## Goal

A job that gives up leaves one row saying which job, when, after how many attempts and what kind of error, with no payload content.

## Why this ticket exists

Logs scroll away. A small table makes permanent failures countable (for the status endpoint) and reviewable later, and it is the trigger for alerts.

## Read first

- `api/app/telegram/models.py`, `repository.py`.
- `api/migrations/env.py`: register the new models module.

## Design

- **Pattern:** Repository.
- **Data flow:** `on_job_failed(...)` → `record_failure(session, …)` → row.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/models.py` (new), `api/app/jobs/repository.py` (new); generated revision `create job_failures`; `api/migrations/env.py` (changed).
- `api/app/jobs/broker.py` (changed): the hook calls `record_failure`.
- `api/tests/test_job_failures.py` (new).

**Table `job_failures`**

| Column | Type | Rules |
|---|---|---|
| `id` | UUID | primary key |
| `job` | `String(60)` | not null |
| `job_id` | `String(120)` | not null |
| `attempts` | `SmallInteger` | not null |
| `error_type` | `String(80)` | the exception class name |
| `failed_at` | timestamptz | `server_default=func.now()`; indexed |

No payload and no exception message: messages can contain user content.

**Functions**

- `async def record_failure(session, job, job_id, attempts, error_type) -> None`
- `async def count_failures_since(session, since: datetime) -> int`
- `async def delete_failures_before(session, cutoff: datetime) -> int`

The hook opens its own session, so a failure is recorded even when the job's session was rolled back. If recording itself fails, log `job.failure_not_recorded` and carry on.

## Steps

1. Model and migration.
2. The three repository functions.
3. Call `record_failure` from the hook.
4. Tests.

## Tests

- `test_record_failure_stores_row`
- `test_no_payload_or_message_column_exists`
- `test_count_failures_since`
- `test_delete_failures_before`
- `test_final_failure_of_a_job_creates_exactly_one_row`
- `test_recording_error_does_not_crash_the_worker`

## Acceptance criteria

- [ ] A permanently failed job leaves exactly one row
- [ ] The table cannot hold payloads or error messages
- [ ] `downgrade` removes the table
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-migrate
```

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The columns: nothing that could carry user content.
2. The hook uses its own session.

Things that should *not* be in the diff: alerts, an endpoint.

## Out of scope

- Clean-up → BE-055.
- Status → BE-056.
- Alert → BE-057.

## Notes / log

The agent adds progress notes, decisions and open questions here.
