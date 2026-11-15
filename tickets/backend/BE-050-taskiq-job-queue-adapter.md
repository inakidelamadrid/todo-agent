# BE-050: JobQueue adapter: enqueue once, optionally later

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-049
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~12 min

## Goal

The real `JobQueue` sends jobs through taskiq, accepts each `job_id` only once, and supports `run_at`.

## Why this ticket exists

This is the piece features will actually receive. The two behaviours that matter to them, "never twice" and "not before this time", are implemented here once.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- `api/app/jobs/queue.py` (BE-047) and `broker.py`.
- Redis `SET key value NX EX seconds`: sets the key only if it does not exist. It is an atomic "have I seen this?" check, the same idea as `claim_update` in BE-011.

## Design

- **Pattern:** Adapter + idempotency key.
- **Data flow:** `enqueue(request)` → `SET jobs:id:<job_id> NX EX` → not set: `False`; set: send now, or schedule for `run_at` → `True`.

## Packages

None new. Standard library and what is already installed.

Hand-written instead of a package: the once-only check, about 10 lines over Redis `SET NX`. taskiq does not, to my knowledge, refuse duplicate task IDs by itself; confirm, and use a built-in if one exists.

## Details

**Files**

- `api/app/jobs/taskiq_queue.py` (new): `taskiq_job_queue(redis: Redis, ...) -> JobQueue`.
- `api/app/main.py` (changed): broker start-up and shutdown in the lifespan; `app.state.job_queue`. `api/app/jobs/queue.py` (changed): `get_job_queue(request) -> JobQueue`.
- `api/tests/test_taskiq_job_queue.py` (new).

**`enqueue`**

1. `SET jobs:id:<job_id> 1 NX EX 604800` (7 days). Not set → return `False`.
2. `run_at is None` or in the past → send `run_job(name, payload)` now.
3. `run_at` in the future → schedule it for that time using taskiq's supported mechanism for one-off delayed tasks (confirm in the docs; record the choice in the log). Requires the scheduler process from BE-052 to be running; until then a delayed job is stored and not run, and the ticket says so in its docstring.
4. If sending fails, delete the `jobs:id:` key so the caller can retry, then raise `JobEnqueueFailed`.

Under tests the adapter is exercised with the in-memory broker and the Docker Redis (per-worker key prefix, as in BE-017).

## Steps

1. The once-only check with its tests.
2. Immediate sends.
3. Delayed sends.
4. Failure clean-up.
5. Lifespan wiring and the dependency.

## Tests

- `test_enqueue_sends_job_and_returns_true`
- `test_same_job_id_twice_sends_once_and_returns_false`
- `test_concurrent_enqueue_same_id_sends_once`
- `test_past_run_at_sends_now`
- `test_future_run_at_is_scheduled_not_sent`
- `test_send_failure_releases_the_job_id`

## Acceptance criteria

- [ ] A `job_id` is accepted at most once in 7 days, including under concurrent calls
- [ ] A failed send does not burn the `job_id`
- [ ] Features depend on `get_job_queue`, never on taskiq
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

By hand: run the ping script from BE-049 twice with the same job ID; the worker runs it once.

## Review guide

Read the diff in this order, and check:

1. The order: claim the ID, then send, and the release on failure.
2. How delayed jobs are scheduled, per the log note.
3. `main.py`: started once, shut down once.

Things that should *not* be in the diff: retries, periodic schedules.

## Out of scope

- Periodic jobs and the scheduler process → BE-052.
- Retries → BE-053.

## Assumptions

- Job IDs are remembered for 7 days. Use IDs that include a date or period (`radar:digest:2026-11-15`) so legitimate repeats are distinct.

## Notes / log

The agent adds progress notes, decisions and open questions here.
