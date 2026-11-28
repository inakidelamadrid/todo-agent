# BE-085: GET /tasks and GET /tasks/{id}

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §8 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-084
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~10 min

## Goal

`GET /tasks` and `GET /tasks/{id}` return tasks to a signed-in owner or an API-key machine, and nothing to anyone else.

## Why this ticket exists

First visible piece of M2: the tasks router exists and is mounted behind `require_principal`. Later route tickets add to this router.

## Read first

- `api/app/bills/router.py`: thin controller, `_bill_or_404`, `Session` alias.
- `api/app/main.py`: routers mounted with `dependencies=[Depends(require_principal)]`.
- `api/tests/test_bills_api.py`: how auth is tested (missing key, wrong key, bearer token).

## Design

- **Pattern:** Thin controller: validate → repository → schema.
- **Data flow:** `GET /tasks?status=…` → `list_tasks` → `list[TaskOut]`.

## Packages

None new.

## Details

**Files:** `api/app/tasks/router.py` (new), `api/app/main.py` (changed: mount `tasks_router` with `require_principal`), `api/tests/test_tasks_api.py` (new).

| Request | Response |
|---|---|
| `GET /tasks` | `200` `TaskOut[]`, `active` + `snoozed` |
| `GET /tasks?status=done&status=dropped` | `200` only those statuses (repeatable query param) |
| `GET /tasks?parentId=<uuid>` | `200` children of that task |
| `GET /tasks?status=bogus` | `422` |
| `GET /tasks/{id}` | `200` `TaskOut`; `404 {"detail":"Task not found"}` |
| no credentials / wrong key | `401` |

`_task_or_404(session, id)` helper, as in bills.

## Steps

1. Router with both routes and the helper.
2. Mount in `main.py`.
3. Tests.

## Tests

- `test_list_tasks_empty`
- `test_list_tasks_filters_by_status`
- `test_get_task_404`
- `test_tasks_require_credentials` → missing key `401`
- `test_tasks_reject_wrong_key` → `401`
- `test_tasks_accept_owner_bearer_token` → `200`

## Acceptance criteria

- [ ] Both routes return the shapes above
- [ ] Endpoints reject requests without valid credentials (missing and wrong key → `401`)
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make api-dev`, open <http://127.0.0.1:8000/docs>, authorise with your API key, call `GET /tasks` → `200 []`. Without authorising → `401`.

## Review guide

1. `main.py`: mounted with `require_principal`, like bills.
2. Router: no logic beyond 404 and calling the repository.

Things that should *not* be in the diff: POST/PATCH/DELETE (BE-086/087).

## Out of scope

- Create → BE-086.

## Notes / log
