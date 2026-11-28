# BE-082: tasks table and migration

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §7 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-080
- **Can run in parallel with:** BE-081
- **Public endpoint?** no
- **Review size:** ~90 lines (plus generated migration), 3 files, ~10 min

## Goal

A `tasks` table exists in Postgres, with CHECK constraints that mirror BE-080's limits and a one-level `parent_id` self-reference.

## Why this ticket exists

The repository (BE-083/084) needs a table. Doing the model and migration alone keeps the review focused on columns and constraints.

## Read first

- `api/app/bills/models.py`: CHECKs built from the enums and constants, `server_default=func.now()`.
- `RUNBOOK-migrations.md` and `api/migrations/versions/c983c9c12143_create_bills_and_payments.py`.

## Design

- **Pattern:** none; persistence schema. The database enforces the same contract as the API.

## Packages

None new.

## Details

**Files:** `api/app/tasks/models.py` (new), `api/migrations/versions/<rev>_create_tasks.py` (generated with `make api-revision m="create tasks"`, then reviewed), `api/migrations/env.py` (changed only if models must be imported there for autogenerate), `api/tests/test_task_models.py` (new).

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | default `uuid4` |
| `title` | varchar(120) | `char_length BETWEEN 1 AND 120` |
| `notes` | varchar(2000) | default `''` |
| `size`, `energy`, `context`, `status` | varchar(10) | `IN (…)` from the enums |
| `do_date`, `due_date`, `snoozed_until` | date, nullable | — |
| `first_step` | varchar(200) | default `''` |
| `parent_id` | UUID, nullable | FK `tasks.id` `ON DELETE CASCADE` |
| `created_from` | UUID, nullable | no FK (the inbox table arrives in BE-092; the link is informational) |
| `completed_at`, `dropped_at` | timestamptz, nullable | — |
| `created_at`, `updated_at` | timestamptz | server `now()`; `updated_at` onupdate |

Extra CHECKs: `parent_id <> id`; `status <> 'snoozed' OR snoozed_until IS NOT NULL`.

Indexes: `ix_tasks_status`, `ix_tasks_parent_id`, `ix_tasks_due_date`.

The "only one level deep" rule needs a lookup, so it lives in the repository (BE-084), not a CHECK.

## Steps

1. Model.
2. Generate the migration; read it; remove noise.
3. `make api-migrate` on a dev DB; downgrade and upgrade again.
4. Tests.

## Tests

- `test_tasks_check_rejects_empty_title` (insert with raw SQL → IntegrityError)
- `test_snoozed_requires_snoozed_until`
- `test_deleting_parent_cascades_to_children`
- `test_migration_upgrade_downgrade_roundtrip` (if the suite already has a migration helper; otherwise a manual step)

## Acceptance criteria

- [ ] `make api-migrate` creates the table; `alembic downgrade -1` drops it cleanly
- [ ] Every CHECK in the table exists
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make db-up && make api-migrate && make db-psql
\d tasks
```

The columns, CHECKs and the self-FK with `ON DELETE CASCADE` are listed.

## Review guide

1. Model: CHECKs built from the BE-080 enums/constants, not retyped.
2. Migration: only `tasks`, nothing else; downgrade drops indexes and table.

Things that should *not* be in the diff: repository functions, routes.

## Out of scope

- Repository → BE-083/084.

## Notes / log
