# BE-088: Task status actions: complete, snooze, drop, reopen

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4, §8 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-081, BE-087
- **Can run in parallel with:** M4 tickets
- **Public endpoint?** no
- **Review size:** ~100 lines, 3 files, ~10 min

## Goal

`POST /tasks/{id}/complete | snooze | drop | reopen` move a task through its lifecycle using BE-081's table, and illegal moves return `409`.

## Why this ticket exists

This finishes M2 and gives the UI (M3), What now? "Not today" (BE-106) and focus Done (BE-108) one shared way to change status.

## Read first

- `api/app/tasks/domain.py` (BE-081): `transition`.
- `api/app/bills/router.py`: idempotent upsert style for comparison.

## Design

- **Pattern:** State machine: the route asks `transition`, the repository applies it.
- **Data flow:** route → `transition(task.status, event)` → `None` → `409` | new status → `apply_status(session, task, status, snoozed_until, now)` → `TaskOut`.

## Packages

None new.

## Details

**Files:** `api/app/tasks/repository.py` (changed: `apply_status`), `api/app/tasks/router.py` (changed), `api/tests/test_task_actions_api.py` (new).

```python
async def apply_status(session, task: Task, status: TaskStatus, *, snoozed_until: date | None = None) -> Task
```

Sets `status`; `completed_at = now()` when entering `done`, cleared when leaving; `dropped_at` likewise for `dropped`; `snoozed_until` set for `snoozed`, cleared otherwise.

| Request | Body | Result |
|---|---|---|
| `POST /tasks/{id}/complete` | — | `200`, `done` |
| `POST /tasks/{id}/snooze` | `{"until":"2026-11-23"}` | `200`, `snoozed` |
| `POST /tasks/{id}/drop` | — | `200`, `dropped` |
| `POST /tasks/{id}/reopen` | — | `200`, `active` |
| illegal move (e.g. complete a done task) | — | `409 {"detail":"Can't complete a task that is done"}` |
| unknown id | — | `404` |
| no / wrong credentials | — | `401` |

A past `until` is accepted: the task is simply awake again (`is_awake`), which is harmless.

## Steps

1. `apply_status`.
2. The four routes sharing one helper `_act(task_id, event, **kw)`.
3. Tests.

## Tests

- `test_complete_sets_completed_at`
- `test_complete_twice_409`
- `test_snooze_requires_until_422`
- `test_reopen_dropped_task_clears_dropped_at`
- `test_actions_404`
- `test_actions_require_credentials`

## Acceptance criteria

- [ ] Every action uses `transition`; no status `if` chains in the router
- [ ] Timestamps follow the rules above
- [ ] Endpoints reject requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

M2 demo in `/docs`: create a task → complete → `status: "done"` with `completedAt` → complete again → `409` → reopen → `active`.

## Review guide

1. `_act`: one path for all four actions?
2. `apply_status`: timestamps cleared when leaving a state?

Things that should *not* be in the diff: focus sessions, suggestions.

## Out of scope

- Recurring tasks rolling forward → deferred.

## Notes / log
