# BE-086: POST /tasks

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §8 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-085
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files, ~8 min

## Goal

`POST /tasks` creates a task (or a subtask) and returns it.

## Why this ticket exists

With this, you can fill the tasks table from `/docs` for every later demo, before the inbox exists.

## Read first

- `api/app/bills/router.py`: the create route and `status_code=201`.

## Design

- **Pattern:** Thin controller. `ParentProblem` from BE-084 maps to `422`.

## Packages

None new.

## Details

**Files:** `api/app/tasks/router.py` (changed), `api/tests/test_tasks_api.py` (changed).

Request:

```json
{"title":"Call dentist","size":"S","energy":"low","context":"phone","dueDate":"2026-11-28","firstStep":"Find the number"}
```

| Case | Response |
|---|---|
| valid | `201` `TaskOut` (`status: "active"`) |
| invalid field | `422` (FastAPI detail) |
| `parentId` unknown | `422 {"detail":"Parent task not found"}` |
| `parentId` is itself a subtask | `422 {"detail":"Subtasks can only be one level deep"}` |
| no / wrong credentials | `401` |

## Steps

1. Route.
2. Tests.

## Tests

- `test_create_task_201`
- `test_create_task_invalid_title_422`
- `test_create_subtask_too_deep_422`
- `test_create_task_requires_credentials` (missing and wrong key → `401`)

## Acceptance criteria

- [ ] Responses as in the table
- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

In `/docs`: `POST /tasks` with the example → `201`; `GET /tasks` lists it. Create a subtask of it, then a subtask of that subtask → `422`.

## Review guide

1. The `ParentProblem` → `422` mapping: one place, clear messages.

Things that should *not* be in the diff: PATCH/DELETE.

## Out of scope

- PATCH/DELETE → BE-087.

## Notes / log
