# BE-092: dumps and inbox_items tables

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2, §7 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-089
- **Can run in parallel with:** BE-090, BE-093
- **Public endpoint?** no
- **Review size:** ~100 lines (plus generated migration), 3 files, ~10 min

## Goal

`dumps` keeps every raw dump; `inbox_items` keeps the candidate items parsed from it.

## Why this ticket exists

"No lost items" and "I can always see what I originally said" need the raw text stored next to its items. Schema only; the repository is BE-094.

## Read first

- `api/app/bills/models.py`, `api/app/telegram/models.py`: CHECKs from enums; JSON column usage if any.
- `RUNBOOK-migrations.md`.

## Design

- **Pattern:** none; persistence schema. `payload` is JSONB validated by `ItemPayload` at the edge (the DB checks only `type`).

## Packages

None new.

## Details

**Files:** `api/app/inbox/models.py` (new), `api/migrations/versions/<rev>_create_dumps_and_inbox_items.py` (generated), `api/tests/test_inbox_models.py` (new).

**`dumps`**

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `raw_text` | varchar(4000) | length 1–4000 |
| `source` | varchar(20) | `IN` DumpSource values |
| `source_ref` | varchar(100) | default `''` (Telegram message id later) |
| `received_at` | timestamptz | server `now()` |

**`inbox_items`**

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `dump_id` | UUID | FK `dumps.id` `ON DELETE CASCADE` |
| `type` | varchar(10) | `IN` InboxItemType values |
| `payload` | JSONB | `payload->>'type' = type` |
| `confidence` | double precision | `BETWEEN 0 AND 1` |
| `source_span` | varchar(4000) | default `''` |
| `status` | varchar(10) | `IN` InboxItemStatus; default `new` |
| `snoozed_until` | timestamptz nullable | required when `status = 'snoozed'` |
| `created_at`, `updated_at` | timestamptz | server `now()` |

Index: `ix_inbox_items_status_created_at (status, created_at DESC)`.

## Steps

1. Models.
2. Generate and read the migration.
3. Upgrade/downgrade on a dev DB.
4. Tests.

## Tests

- `test_payload_type_must_match_column`
- `test_confidence_bounds`
- `test_deleting_dump_cascades_items`
- `test_snoozed_requires_snoozed_until`

## Acceptance criteria

- [ ] `make api-migrate` creates both tables; downgrade drops them
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-migrate && make db-psql
\d inbox_items
```

Shows the FK to `dumps` with `ON DELETE CASCADE` and the CHECKs.

## Review guide

1. The `payload->>'type' = type` check.
2. Migration touches only these two tables.

Things that should *not* be in the diff: repository, routes.

## Out of scope

- Raw voice/photo storage → not stored (decision 6: discard after parsing).

## Notes / log
