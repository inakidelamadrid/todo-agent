# BE-107: Focus session schemas and table

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.6, §7 · Milestone M11 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-082
- **Can run in parallel with:** M9, M10 tickets
- **Public endpoint?** no
- **Review size:** ~100 lines (plus generated migration), 4 files, ~10 min

## Goal

A focus session (task, planned minutes, start, end, outcome) has frozen schemas and a `focus_sessions` table.

## Why this ticket exists

Sessions record what happened when you started a task (and feed EPIC-005's weekly stats). Schema and table together are small enough for one review.

## Read first

- `api/app/tasks/schemas.py`, `api/app/tasks/models.py` (BE-080, BE-082).

## Design

- **Pattern:** Immutable value objects.

## Packages

None new.

## Details

**Files:** `api/app/focus/__init__.py`, `api/app/focus/schemas.py`, `api/app/focus/models.py` (new), `api/migrations/versions/<rev>_create_focus_sessions.py` (generated), `api/tests/test_focus_schemas.py` (new).

```python
class FocusOutcome(StrEnum): DONE="done"; MORE_TIME="more-time"; STUCK="stuck"; ABANDONED="abandoned"
class FocusSessionCreate(_CamelModel): task_id: UUID; planned_minutes: Annotated[int, Field(ge=1, le=180)]
class FocusSessionEnd(_CamelModel): outcome: FocusOutcome
class FocusSessionOut: id, task_id, planned_minutes, started_at, ended_at | None, outcome | None
```

The UI offers 10 / 25 / 45 (decision 3); the API accepts 1–180 so "need more time" can add any amount.

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `task_id` | UUID | FK `tasks.id` `ON DELETE CASCADE` |
| `planned_minutes` | int | `BETWEEN 1 AND 180` |
| `started_at` | timestamptz | server `now()` |
| `ended_at` | timestamptz nullable | |
| `outcome` | varchar(10) nullable | enum values; `(outcome IS NULL) = (ended_at IS NULL)` |

## Steps

1. Schemas + tests.
2. Model + migration.

## Tests

- `test_planned_minutes_bounds`
- `test_unknown_outcome_rejected`
- `test_outcome_and_ended_at_set_together` (DB CHECK)

## Acceptance criteria

- [ ] `make api-migrate` creates the table; downgrade drops it
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "from app.focus.schemas import FocusSessionEnd as E; E(outcome='maybe')"
```

Raises a `ValidationError`. Then `make api-migrate` and `\d focus_sessions` in `make db-psql`.

## Review guide

1. The paired CHECK on `outcome` / `ended_at`.

## Out of scope

- Routes → BE-108. Telegram check-in → deferred.

## Notes / log
