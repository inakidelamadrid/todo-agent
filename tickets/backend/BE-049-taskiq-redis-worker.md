# BE-049: Redis broker and the worker process (make worker-dev)

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-017, BE-048
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 4 files, ~10 min

## Goal

Jobs travel through Redis, and a separate worker process started with `make worker-dev` picks them up and runs them.

## Why this ticket exists

Until now jobs ran inside the test process. Real background work needs a second process, so a slow job never delays a web request and jobs survive an API restart. This ticket adds that process and nothing else.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- https://github.com/taskiq-python/taskiq-redis: which broker classes exist and which acknowledge messages.
- `api/app/redis.py` and the Redis settings from BE-017.
- `Makefile`: `api-dev` as the model for a run target.

## Design

- **Pattern:** Adapter: the broker is built from settings by a factory function; tests keep the in-memory broker.
- **Data flow:** API process → Redis → worker process (`taskiq worker app.jobs.broker:broker`) → `run_job`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `taskiq-redis` | **new** | Redis broker for taskiq | 1.2.4, MIT, released 2026-09-28. The official Redis integration; requires `redis>=8,<9`, matching BE-017. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add taskiq-redis`.
- `api/app/jobs/broker.py` (changed): `build_broker(settings) -> AsyncBroker`.
- `Makefile` (changed): `worker-dev`. `api/README.md` (changed): a short "Background worker" section.
- `api/tests/test_jobs_broker.py` (changed).

**`build_broker`**

- When `settings.jobs_in_memory` is true (a new setting, default `False`, set to `True` by the test fixtures) → the in-memory broker.
- Otherwise → a Redis broker built from the BE-017 Redis settings. Choose the broker class that **acknowledges** messages (a job taken by a worker that crashes is redelivered), and say which and why in the ticket log.
- The Redis password is passed from `SecretStr` and never logged; the connection URL is never printed.

**Make**

```make
worker-dev: check-db-running ## Start the background worker (needs make db-up)
```
Runs the taskiq worker for `app.jobs.broker:broker` from `api/`.

**Manual check job.** A tiny script `api/scripts/enqueue_ping.py` sends `system.ping` through the real broker so the hand verification below is one command.

## Steps

1. Check `taskiq-redis` on PyPI again; add it.
2. `build_broker` and the `jobs_in_memory` setting.
3. `make worker-dev` and the README section.
4. The ping script.
5. Run it by hand.

## Tests

- `test_build_broker_is_in_memory_under_tests`
- `test_build_broker_uses_redis_settings_otherwise`: asserts the type and that the password does not appear in `repr`.
- Existing BE-048 tests pass unchanged.

## Acceptance criteria

- [ ] `taskiq-redis` is a runtime dependency and `redis` stays on 8.x in the lockfile
- [ ] `make worker-dev` starts a worker that runs `system.ping`
- [ ] The test suite needs no worker process
- [ ] The chosen broker class redelivers a job when a worker dies mid-run
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make db-up
```

```bash
make worker-dev
```

In a second terminal, from `api/`:

```bash
uv run python -m scripts.enqueue_ping
```

The worker terminal shows the job being received and completed.

## Review guide

Read the diff in this order, and check:

1. `build_broker`: two branches.
2. The lockfile: `redis` is still 8.x.
3. The log note on which broker class was chosen and why.
4. The make target.

Things that should *not* be in the diff: schedules, retries, our `JobQueue` adapter.

## Out of scope

- `JobQueue.enqueue` over this broker → BE-050.
- Production process management → undecided with hosting.

## Notes / log

The agent adds progress notes, decisions and open questions here.
