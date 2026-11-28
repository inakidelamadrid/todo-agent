# BE-081: Task status state machine and size rules

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-080
- **Can run in parallel with:** BE-082
- **Public endpoint?** no (no routes)
- **Review size:** ~90 lines, 2 files, ~10 min

## Goal

`api/app/tasks/domain.py` holds the pure rules: which status moves are legal, how many minutes each size means, and whether a snoozed task is awake today.

## Why this ticket exists

Several routes change a task's status (complete, snooze, drop, reopen, "Not today", focus Done). If each route decided legality itself, the rules would drift. One transition table, tested alone, is the single answer. Size→minutes is reused by What now? (BE-101).

## Read first

- `api/app/bills/domain.py`: pure functions, no I/O, plain types.
- **State machine:** a table of `(state, event) → new state`; anything not in the table is illegal. Callers ask the table instead of writing `if` chains.

## Design

- **Pattern:** State machine (transition table + one pure `transition` function) and Result over exceptions (returns `None` for illegal moves; the route turns that into `409`).
- **Data flow:** route → `transition(current, event)` → new status or `None`.

## Packages

None new.

## Details

**Files:** `api/app/tasks/domain.py` (new), `api/tests/test_task_domain.py` (new).

```python
class TaskEvent(StrEnum):
    COMPLETE = "complete"; SNOOZE = "snooze"; WAKE = "wake"; DROP = "drop"; REOPEN = "reopen"

TRANSITIONS: Mapping[tuple[TaskStatus, TaskEvent], TaskStatus]  # MappingProxyType
```

| From \ event | complete | snooze | wake | drop | reopen |
|---|---|---|---|---|---|
| `active` | done | snoozed | — | dropped | — |
| `snoozed` | done | snoozed (new date) | active | dropped | — |
| `done` | — | — | — | — | active |
| `dropped` | — | — | — | — | active |

Functions (all pure):

- `transition(status: TaskStatus, event: TaskEvent) -> TaskStatus | None`
- `SIZE_MINUTES: Mapping[TaskSize, int | None] = {XS: 5, S: 15, M: 45, L: 120, XL: None}` (`None` = needs breaking down; never fits a time box).
- `is_awake(status: TaskStatus, snoozed_until: date | None, today: date) -> bool`: `active`, or `snoozed` with `snoozed_until <= today`. Snoozed tasks wake lazily (no job needed).

## Steps

1. Event enum and table.
2. `transition`, `SIZE_MINUTES`, `is_awake`.
3. Tests, including a test that walks every cell of the table.

## Tests

- `test_every_legal_transition_matches_table` (parametrised over the table)
- `test_illegal_transitions_return_none` (e.g. `done` + `snooze`, `active` + `reopen`)
- `test_size_minutes_xl_is_none`
- `test_snoozed_task_wakes_on_its_date`
- `test_snoozed_task_sleeps_before_its_date`

## Acceptance criteria

- [ ] The module has no imports from SQLAlchemy, FastAPI or `app.db`
- [ ] Every cell of the table is covered by a test
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "from app.tasks.domain import *; from app.tasks.schemas import TaskStatus as S; print(transition(S.DONE, TaskEvent.SNOOZE), transition(S.ACTIVE, TaskEvent.COMPLETE), SIZE_MINUTES['M'])"
```

Prints `None done 45`.

## Review guide

1. The table: read it against the epic's §5.4 lifecycle. Is "dropped isn't failure" honoured (reopen allowed)?
2. `is_awake`: inclusive on the date?

Things that should *not* be in the diff: timestamps (`completedAt` is set by the repository, BE-088).

## Out of scope

- Applying transitions to rows → BE-088.

## Notes / log
