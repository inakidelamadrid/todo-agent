# BE-083: Task repository: list and get

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-082
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~50 lines, 2 files, ~6 min

## Goal

`list_tasks` and `get_task` read tasks from the database.

## Why this ticket exists

Reads come before writes so the first route (BE-085) can ship early. Two small functions keep the review to the query shape.

## Read first

- `api/app/bills/repository.py`: functions take a session and do one thing.

## Design

- **Pattern:** Repository (a module of async functions, no class).

## Packages

None new.

## Details

**Files:** `api/app/tasks/repository.py` (new), `api/tests/test_task_repository.py` (new).

```python
async def list_tasks(
    session: AsyncSession,
    statuses: Collection[TaskStatus] = (TaskStatus.ACTIVE, TaskStatus.SNOOZED),
    parent_id: UUID | None = None,
) -> list[Task]
```

Order: `due_date NULLS LAST, do_date NULLS LAST, created_at, id`. When `parent_id` is given, only its children.

```python
async def get_task(session: AsyncSession, task_id: UUID) -> Task | None
```

## Steps

1. Both functions.
2. Tests with the existing DB fixtures.

## Tests

- `test_list_defaults_to_active_and_snoozed`
- `test_list_orders_by_due_then_do_date`
- `test_list_children_of_parent`
- `test_get_missing_returns_none`

## Acceptance criteria

- [ ] No HTTP or FastAPI imports in the repository
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run pytest -k task_repository -v
```

The four named tests pass.

## Review guide

1. The ordering: does it put dated, urgent tasks first?

Things that should *not* be in the diff: writes (BE-084).

## Out of scope

- Create, update, delete → BE-084.

## Notes / log
