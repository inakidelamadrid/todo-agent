# BE-053: Retry rules for failed jobs

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-051
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 3 files, ~10 min

## Goal

A job that raises is retried a limited number of times with growing delays, and jobs can opt out.

## Why this ticket exists

Background work fails for temporary reasons (a network blip, a restart). Retrying a few times fixes most of it without anyone noticing; retrying forever hides real bugs. The rule is a small pure function so the numbers are easy to see and change.

## Read first

- Confirm every taskiq name used here against https://taskiq-python.github.io/ before coding. The ticket fixes *our* interfaces; the exact taskiq calls behind them are the implementer's to verify, not to recall.
- taskiq's retry middleware options (confirm what exists and what it supports for delays).
- `next_attempt_at` in BE-032: the same idea, applied to outbox rows.

## Design

- **Pattern:** Retry as data: a pure function decides; taskiq's retry mechanism executes the decision.
- **Data flow:** job raises → `retry_decision(job, attempt, error)` → `RetryIn(seconds)` or `GiveUp` → re-send with `attempt + 1`, or hand to BE-054.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/retry.py` (new).
- `api/app/jobs/broker.py` (changed).
- `api/tests/test_job_retry.py` (new).

**Pure function**

```python
MAX_ATTEMPTS = 5

class NoRetry(Exception): ...        # a job raises this for failures that retrying cannot fix

def retry_decision(attempt: int, error: BaseException) -> RetryIn | GiveUp
```

| Case | Result |
|---|---|
| `error` is `NoRetry` or `UnknownJob` | `GiveUp` |
| `attempt >= MAX_ATTEMPTS` | `GiveUp` |
| otherwise | `RetryIn(min(30 * 2 ** (attempt - 1), 900))` seconds: 30, 60, 120, 240 |

**Wiring.** In `run_job`, an exception leads to `retry_decision`. `RetryIn` → re-send the same job with `attempt + 1` after the delay, using taskiq's retry support if it can express the delay, otherwise a delayed send through our own queue. `GiveUp` → call `on_job_failed(name, job_id, attempt, error)`, a hook that only logs for now (BE-054 records it).

Retried runs bypass the once-only check from BE-050: they are the same job, not a duplicate.

**For job authors**, in the module docstring: jobs must be safe to run twice (a crash after the work but before the acknowledgement causes a second run).

## Steps

1. `retry_decision` with the table as tests.
2. Wire it into `run_job`.
3. The `on_job_failed` hook.

## Tests

- `test_delays_double_and_cap`
- `test_gives_up_after_max_attempts`
- `test_no_retry_error_gives_up_immediately`
- `test_failing_job_is_resent_with_incremented_attempt`
- `test_final_failure_calls_hook_once`
- `test_successful_job_is_not_retried`

## Acceptance criteria

- [ ] A failing job runs at most 5 times
- [ ] `NoRetry` stops retries immediately
- [ ] `retry_decision` is pure
- [ ] The final failure reaches exactly one hook call
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The table against `retry_decision`.
2. How the delay is carried out, per the log note.
3. The idempotency note for job authors.

Things that should *not* be in the diff: storing failures; alerting.

## Out of scope

- Recording failures → BE-054.
- Alerting → BE-057.

## Notes / log

The agent adds progress notes, decisions and open questions here.
