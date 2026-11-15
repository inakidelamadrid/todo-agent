# BE-051: Give jobs a database session and the Telegram sender

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-049, BE-019
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~10 min

## Goal

Every job receives a `JobContext` with a fresh database session and the Telegram sender, created and cleaned up by the worker.

## Why this ticket exists

Web requests get their dependencies from FastAPI. The worker is a different process with no FastAPI, so it needs its own small start-up that builds the same things once and hands each job what it needs.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- `api/app/main.py` lifespan and `api/app/db.py`: how the web process builds the engine and sessions.
- `api/app/telegram/aiogram_sender.py`.

## Design

- **Pattern:** Dependency injection by hand: resources are built at worker start-up; the context is assembled per job.
- **Data flow:** worker start → engine, Redis, sender → per job: open session → `JobContext` → job → close session → worker stop → dispose.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/queue.py` (changed): `JobContext` gains `session: AsyncSession`, `sender: TelegramSender`, `redis: Redis`.
- `api/app/jobs/worker.py` (new): start-up and shutdown hooks registered on the broker; `job_context(state, attempt) -> AsyncIterator[JobContext]`, an async context manager that opens a session and always closes it.
- `api/app/jobs/broker.py` (changed): `run_job` uses `job_context`.
- `api/tests/test_job_context.py` (new).

**Rules**

- One engine and one sender per worker process, built with the same functions the web app uses (`build_engine`, `aiogram_sender` / `unconfigured_sender`). No duplicated construction logic.
- One session per job, never shared between jobs. A job that raises still has its session closed and rolled back.
- Structured logging: the worker calls `configure_logging()` (BE-042, if merged) and logs one event per job: `job.done` or `job.failed` with `name`, `job_id`, `attempt`, `latency_ms`, `error_type`. **Never the payload.**
- The test fixtures build a `JobContext` directly with the test session and the recording sender, so job functions are tested without a worker.

## Steps

1. Extend `JobContext`.
2. Worker start-up and shutdown.
3. `job_context` and its use in `run_job`.
4. Logging.
5. Tests.

## Tests

- `test_job_receives_session_and_sender`
- `test_session_is_closed_after_success`
- `test_session_is_rolled_back_and_closed_after_failure`
- `test_each_job_gets_its_own_session`
- `test_job_log_event_has_no_payload`

## Acceptance criteria

- [ ] The worker builds its resources with the same functions as the web app
- [ ] A failing job never leaks a session
- [ ] Job functions can be unit-tested by constructing a `JobContext`
- [ ] No payload content appears in logs
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

Start `make worker-dev`: it starts cleanly with and without `TELEGRAM_BOT_TOKEN` set.

## Review guide

Read the diff in this order, and check:

1. `job_context`: the `finally`.
2. `worker.py`: nothing is constructed differently from `main.py`.
3. The log fields.

Things that should *not* be in the diff: any real job beyond `system.ping`.

## Out of scope

- Scheduled jobs → BE-052.
- The delivery job → BE-031.

## Notes / log

The agent adds progress notes, decisions and open questions here.
