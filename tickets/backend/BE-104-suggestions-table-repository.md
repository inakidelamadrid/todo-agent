# BE-104: suggestions table and repository

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.5, §7 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-082
- **Can run in parallel with:** BE-101–103
- **Public endpoint?** no
- **Review size:** ~110 lines (plus generated migration), 4 files, ~10 min

## Goal

Every suggestion shown is recorded with its inputs and score factors, and the engine can ask "which tasks were skipped recently?".

## Why this ticket exists

"Rerolls avoid recent skips" (epic §10) needs memory of what was shown and skipped. The recorded factors also make any odd suggestion explainable later.

## Read first

- `api/app/inbox/models.py` (BE-092): JSONB column pattern.
- `api/app/bills/repository.py`.

## Design

- **Pattern:** Repository.

## Packages

None new.

## Details

**Files:** `api/app/now/models.py` (new), `api/migrations/versions/<rev>_create_suggestions.py` (generated), `api/app/now/repository.py` (new), `api/tests/test_now_repository.py` (new).

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `task_id` | UUID | FK `tasks.id` `ON DELETE CASCADE` |
| `requested_at` | timestamptz | server `now()` |
| `energy`, `context` | varchar(10) nullable | enum values |
| `available_minutes` | int nullable | `IN (5,15,30,60)` |
| `score_factors` | JSONB | the `Factors` + `total` |
| `action` | varchar(10) nullable | `IN ('started','rerolled','not-today')` |
| `acted_at` | timestamptz nullable | |

Index `ix_suggestions_requested_at`.

```python
async def record_suggestion(session, task_id: UUID, req: NowRequest, scored: Scored) -> Suggestion
async def get_suggestion(session, suggestion_id: UUID) -> Suggestion | None
async def set_action(session, suggestion: Suggestion, action: SuggestionAction) -> Suggestion
async def recent_skipped_task_ids(session, since: datetime) -> frozenset[UUID]   # action in (rerolled, not-today) and acted_at >= since
```

## Steps

1. Model + migration.
2. Repository + tests.

## Tests

- `test_record_stores_factors_json`
- `test_recent_skips_only_within_window`
- `test_recent_skips_ignore_started`
- `test_deleting_task_deletes_suggestions`

## Acceptance criteria

- [ ] `make api-migrate` creates the table; downgrade drops it
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-migrate && make db-psql
\d suggestions
```

## Review guide

1. Migration touches only `suggestions`.
2. `recent_skipped_task_ids` window logic.

## Out of scope

- The route → BE-105.

## Notes / log
