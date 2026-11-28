# BE-084: Task repository: create, update, delete

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-083
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~80 lines, 2 files, ~8 min

## Goal

Tasks can be created, updated and deleted, and a subtask of a subtask is refused.

## Why this ticket exists

The epic allows subtasks "one level deep". That rule needs to look up the parent, so it can't be a CHECK; it lives here, once, before any route uses it.

## Read first

- `api/app/bills/repository.py`: `create_bill`, `update_bill` (`exclude_unset`, `refresh` for `updated_at`), `delete_bill`.

## Design

- **Pattern:** Repository plus Result over exceptions: the depth rule returns a small error value that the route maps to `422`.

## Packages

None new.

## Details

**Files:** `api/app/tasks/repository.py` (changed), `api/tests/test_task_repository.py` (changed).

```python
class ParentProblem(StrEnum):
    NOT_FOUND = "parent-not-found"
    TOO_DEEP = "parent-is-a-subtask"

async def create_task(session, data: TaskCreate) -> Task | ParentProblem
async def update_task(session, task: Task, patch: TaskUpdate) -> Task
async def delete_task(session, task: Task) -> None   # children go with it (FK cascade)
```

- `create_task`: when `data.parent_id` is set, load the parent; missing → `NOT_FOUND`; parent has its own `parent_id` → `TOO_DEEP`. New tasks start `active`.
- `update_task`: `exclude_unset`, then `flush` + `refresh`.

## Steps

1. `create_task` with the parent check.
2. `update_task`, `delete_task`.
3. Tests.

## Tests

- `test_create_task_starts_active`
- `test_create_subtask_of_top_level_task`
- `test_rejects_grandchild_task` → `TOO_DEEP`
- `test_rejects_missing_parent` → `NOT_FOUND`
- `test_update_changes_only_sent_fields`
- `test_delete_removes_children`

## Acceptance criteria

- [ ] Depth rule enforced in one place
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run pytest -k task_repository -v
```

`test_rejects_grandchild_task` is among the passing tests.

## Review guide

1. `create_task`: is the parent lookup the only extra query?
2. `update_task`: can it change `status` or `parent_id`? (It must not; `TaskUpdate` forbids them.)

Things that should *not* be in the diff: routes, status changes.

## Out of scope

- Status transitions → BE-088.

## Notes / log
