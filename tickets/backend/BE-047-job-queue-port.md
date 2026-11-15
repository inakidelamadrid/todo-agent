# BE-047: Job queue port, job registry and an inline fake

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** every EPIC-008 ticket
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~10 min

## Goal

The app has one agreed way to say "run this named job later, once", a registry of job functions, and a fake that runs jobs inline for tests.

## Why this ticket exists

Five epics need background work. If they call the job library directly, the library's vocabulary leaks everywhere and swapping it means touching every feature. This port is the only thing features will ever import; it is defined before any library is installed so it is shaped by our needs, not the library's.

## Read first

- `api/app/telegram/sender.py` (BE-018): the port style (a frozen dataclass of functions) and the recording fake.
- `api/app/telegram/handlers.py` (BE-015): a registry as an immutable mapping.
- A *job* here is a name plus a small JSON payload. The payload holds IDs, never content: the job loads what it needs from the database.

## Design

- **Pattern:** Port + fake; each enqueued job is a command (a frozen description of work to do later).
- **Data flow:** feature → `queue.enqueue(JobRequest)` → later → `JOBS[name](ctx, payload)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/__init__.py` (new, empty), `api/app/jobs/queue.py` (new).
- `api/tests/fakes.py` (changed): `inline_job_queue(...)`.
- `api/tests/test_job_queue_port.py` (new).

**Types**

```python
class JobRequest(BaseModel):                  # frozen
    name: str                                 # ^[a-z][a-z0-9_.]{0,59}$, e.g. "telegram.deliver_due"
    payload: Mapping[str, str | int] = {}     # at most 10 keys; IDs and small values only
    job_id: str                               # 1-120 chars; the same id is accepted only once
    run_at: datetime | None = None            # aware UTC; None = as soon as possible

@dataclass(frozen=True)
class JobContext:
    now: datetime                             # aware UTC, set when the job starts
    attempt: int                              # 1 for the first run

JobFn = Callable[[JobContext, Mapping[str, str | int]], Awaitable[None]]

@dataclass(frozen=True)
class JobQueue:
    enqueue: Callable[[JobRequest], Awaitable[bool]]   # False when job_id was already accepted
```

**Registry**

- `JOBS: Mapping[str, JobFn]`, immutable, empty for now.
- `resolve_job(name: str) -> JobFn`: raises `UnknownJob(name)`.

**Fake.** `inline_job_queue(jobs, now) -> tuple[JobQueue, list[JobRequest]]`: records every request; runs jobs with `run_at is None` immediately through `jobs[name]`; refuses a repeated `job_id` by returning `False`.

`JobContext` grows in BE-051 (database session, Telegram sender). It starts minimal so this ticket has no dependencies.

## Steps

1. Types with their limits.
2. Registry and `resolve_job`.
3. The inline fake.
4. Tests.

## Tests

- `test_job_request_rejects_bad_name_and_oversized_payload`
- `test_job_request_requires_aware_run_at`
- `test_resolve_unknown_job_raises`
- `test_inline_queue_runs_job_once`
- `test_inline_queue_refuses_duplicate_job_id`
- `test_inline_queue_records_but_does_not_run_delayed_jobs`

## Acceptance criteria

- [ ] `api/app/jobs/queue.py` imports no job library
- [ ] A repeated `job_id` is reported as `False`, not an error
- [ ] Payloads are limited to small scalar values
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `JobRequest`: is this enough to express every background need you can think of in the epics (delayed reminder, retryable send, periodic clean-up)?
2. The payload rule: IDs, not content.
3. The fake lives in tests.

Things that should *not* be in the diff: taskiq, Redis, a worker process.

## Out of scope

- The real library → BE-048, BE-049.
- The real adapter → BE-050.

## Notes / log

The agent adds progress notes, decisions and open questions here.
