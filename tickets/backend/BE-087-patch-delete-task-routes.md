# BE-087: PATCH and DELETE /tasks/{id}

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §8 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-086
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~80 lines, 2 files, ~8 min

## Goal

A task's fields can be edited, and a task (with its subtasks) can be deleted.

## Why this ticket exists

Completes plain CRUD before status actions (BE-088) arrive, so each review has one idea.

## Read first

- `api/app/bills/router.py`: PATCH and DELETE.

## Design

- **Pattern:** Thin controller.

## Packages

None new.

## Details

**Files:** `api/app/tasks/router.py` (changed), `api/tests/test_tasks_api.py` (changed).

| Request | Response |
|---|---|
| `PATCH /tasks/{id}` `{"title":"Call the dentist"}` | `200` `TaskOut` |
| `PATCH` with `status` or `parentId` | `422` (forbidden fields) |
| `PATCH {"dueDate": null}` | `200`, due date cleared |
| `DELETE /tasks/{id}` | `204`; children deleted too |
| unknown id | `404` |
| no / wrong credentials | `401` |

"Let go" in the UI is `POST /tasks/{id}/drop` (BE-088), not DELETE; DELETE is for mistakes.

## Steps

1. Both routes.
2. Tests.

## Tests

- `test_patch_task_title`
- `test_patch_rejects_status_422`
- `test_patch_null_clears_due_date`
- `test_delete_task_204_and_children_gone`
- `test_patch_delete_404`
- `test_patch_delete_require_credentials`

## Acceptance criteria

- [ ] Responses as in the table
- [ ] Endpoints reject requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

In `/docs`: rename a task with PATCH, then DELETE it, then `GET /tasks/{id}` → `404`.

## Review guide

1. PATCH: uses `exclude_unset` so a missing field is untouched and an explicit `null` clears it.

Things that should *not* be in the diff: status changes.

## Out of scope

- Complete / snooze / drop / reopen → BE-088.

## Notes / log
