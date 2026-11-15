# BE-048: Add taskiq and run a ping job in memory

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-047
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~60 lines, 3 files, ~10 min

## Goal

taskiq is installed, a broker object exists, and a `ping` job runs through it in tests using taskiq's in-memory broker.

## Why this ticket exists

This is the reviewer's first meeting with taskiq, kept to its two core ideas: a *broker* (where jobs are sent and picked up) and a *task* (a function registered on it). No Redis and no separate process yet, so the library can be understood alone.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- https://taskiq-python.github.io/guide/getting-started.html
- `api/app/jobs/queue.py` from BE-047.

## Design

- **Pattern:** Adapter, first half: one generic taskiq task dispatches to our registry, so features never decorate functions with taskiq.
- **Data flow:** `run_job` task (taskiq) → `resolve_job(name)` → `JobFn(ctx, payload)`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `taskiq` | **new** | Async task queue: brokers, workers, scheduling | 0.13.0, MIT, released 2026-09-26, Python ≥3.10,<4. Chosen over arq (maintenance-only; pins the Redis client below 6) and saq (Redis client below 8). It is the only candidate that works with redis 8.x, which BE-017 installs. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add taskiq`, inside `api/`.
- `api/app/jobs/broker.py` (new).
- `api/tests/test_jobs_broker.py` (new).

**`broker.py`**

- `broker`: an in-memory broker for now. BE-049 replaces how it is built.
- One taskiq task, `run_job(name: str, payload: dict, attempt: int = 1) -> None`: builds a `JobContext(now=datetime.now(UTC), attempt=attempt)`, calls `resolve_job(name)(ctx, payload)`. This is the **only** function in the codebase decorated as a taskiq task.
- `UnknownJob` propagates (a job name with no function is a bug to surface, not to swallow).

**A first job**, registered in `JOBS`: `system.ping`, which does nothing and returns. It exists to prove the path end to end and stays as a health probe.

Reading `datetime.now` inside `run_job` is the edge: the job functions themselves receive `now` in the context and stay testable.

## Steps

1. Check taskiq on PyPI again; `uv add taskiq`.
2. Create the broker and the `run_job` task.
3. Register `system.ping`.
4. Tests using the in-memory broker.

## Tests

- `test_run_job_dispatches_to_registry`: a spy job registered for the test receives its payload.
- `test_run_job_passes_attempt_and_aware_now`
- `test_unknown_job_name_raises`
- `test_ping_job_completes`

## Acceptance criteria

- [ ] `taskiq` is a runtime dependency
- [ ] `broker.py` is the only module that imports taskiq
- [ ] Exactly one function is decorated as a taskiq task
- [ ] Tests need no Redis and no worker process
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `pyproject.toml`: one new line.
2. `broker.py`: one broker, one task. Can you explain both in a sentence each?
3. No feature code changed.

Things that should *not* be in the diff: Redis, a worker command, schedules, retries.

## Out of scope

- Redis and the worker process → BE-049.
- Our `JobQueue` backed by taskiq → BE-050.

## Notes / log

The agent adds progress notes, decisions and open questions here.
