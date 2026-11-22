# BE-069: `playground_actions` table and its two repository functions

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-065 to BE-068
- **Public endpoint?** no
- **Review size:** ~60 lines, 3 files plus a migration, ~10 min

## Goal

A `playground_actions` table records who used which playground tool and how it ended, with no content, plus `record_action` and `count_actions_since`.

## Why this ticket exists

The epic requires every playground action to be recorded. The same table gives the send-test-message tool its hourly limit (BE-079) without a second mechanism.

## Read first

- `api/app/bills/models.py` and `repository.py`: the model and repository style.
- `RUNBOOK-migrations.md`: how a revision is made and reviewed.
- `api/migrations/env.py`: where model modules are imported.

## Design

- **Pattern:** Repository: functions that take a session and do one thing.
- **Data flow:** route → `record_action(session, admin_user_id, tool, outcome)` → row.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/playground/models.py` (new). If `api/app/telegram/playground/` does not exist yet (BE-068 not merged), create the package with empty `__init__.py` files.
- `api/app/telegram/playground/repository.py` (new).
- `api/migrations/env.py` (changed): import the models module.
- `api/migrations/versions/<rev>_create_playground_actions.py` (generated with `make api-revision m="create playground_actions"`, then read and tidied).

**Table `playground_actions`**

| Column | Type | Rules |
|---|---|---|
| `id` | UUID | primary key, server default |
| `admin_user_id` | `String(64)` | not null |
| `tool` | `String(20)` | CHECK: `updates`, `explain`, `replay`, `template_preview`, `test_message` |
| `outcome` | `String(10)` | CHECK: `ok`, `failed`, `rejected` |
| `created_at` | timestamptz | `server_default=func.now()` |

Index on `(tool, created_at)`. **No** request body, message text, template data or chat ID is stored.

**Functions**

```python
async def record_action(session: AsyncSession, admin_user_id: str, tool: str, outcome: str) -> UUID
async def count_actions_since(session: AsyncSession, tool: str, since: datetime, outcome: str = "ok") -> int
```

## Steps

1. Write the model, generate and tidy the migration.
2. Write the two functions.
3. Integration tests with the database fixtures.
4. `make api-migrate` and `make api-test`.

## Tests

- `test_record_action_inserts_a_row_and_returns_its_id`.
- `test_unknown_tool_or_outcome_is_rejected_by_the_database`.
- `test_count_actions_since_counts_only_that_tool_outcome_and_window`.
- `test_migration_upgrade_and_downgrade`.

## Acceptance criteria

- [ ] The migration creates and drops the table cleanly
- [ ] `record_action` and `count_actions_since` work as specified
- [ ] The table has no column that could hold message content
- [ ] The CHECK constraints reject unknown tools and outcomes
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make db-up && make api-migrate`.
2. `make db-psql`, then `\d playground_actions`: the five columns and the index.
3. `make api-test`: green.

## Review guide

Read the diff in this order, and check:

1. The migration: only this table, with a working downgrade?
2. `models.py`: is there any free-text column? There should be none.
3. `repository.py`: one job per function.

Things that should *not* be in the diff: Routes, an endpoint to read the actions, clean-up of old rows.

## Out of scope

- Reading the action record in the UI → later tool.
- Deleting old rows → the daily clean-up job (BE-055) can add it.

## Notes / log

The agent adds progress notes, decisions and open questions here.
