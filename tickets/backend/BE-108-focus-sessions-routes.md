# BE-108: POST /focus-sessions and PATCH /focus-sessions/{id}

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 11, §5.6, §8 · Milestone M11 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-088, BE-107
- **Can run in parallel with:** M10 tickets
- **Public endpoint?** no
- **Review size:** ~120 lines, 4 files, ~12 min

## Goal

Starting a focus session records it; ending it records the outcome, and **Done** also completes the task in the same transaction.

## Why this ticket exists

Backend half of M11. Reuses BE-088's transition so "done from focus" and "done from the list" are the same thing.

## Read first

- `api/app/tasks/domain.py`, `apply_status` (BE-088); `api/app/focus/` (BE-107).

## Design

- **Pattern:** Thin controller + repository; status via `transition`.

## Packages

None new.

## Details

**Files:** `api/app/focus/repository.py` (new: `start_session`, `get_session_by_id`, `end_session`), `api/app/focus/router.py` (new), `api/app/main.py` (changed: mount with `require_principal`), `api/tests/test_focus_api.py` (new).

| Request | Response |
|---|---|
| `POST /focus-sessions {"taskId":"…","plannedMinutes":25}` | `201 FocusSessionOut` |
| task not active (done, dropped, or still snoozed) | `409 {"detail":"This task isn't active"}` |
| unknown task | `404` |
| `PATCH /focus-sessions/{id} {"outcome":"done"}` | `200`; session ended; task `done` |
| outcome `more-time` / `stuck` / `abandoned` | `200`; session ended; task unchanged |
| session already ended | `409` |
| unknown session | `404` |
| no / wrong credentials | `401` |

## Steps

1. Repository.
2. Routes + mount.
3. Tests.

## Tests

- `test_start_session_201`
- `test_start_on_done_task_409`
- `test_end_done_completes_task`
- `test_end_stuck_leaves_task_active`
- `test_end_twice_409`
- `test_focus_requires_credentials`

## Acceptance criteria

- [ ] Ending with `done` and completing the task commit together
- [ ] Endpoints reject requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

In `/docs`: start a session for a task, PATCH with `done` → `GET /tasks/{id}` is `done`.

## Review guide

1. Done path uses `transition`.
2. One commit for both writes.

## Out of scope

- Stats for EPIC-005 → EPIC-005.

## Notes / log
