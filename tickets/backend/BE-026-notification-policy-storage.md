# BE-026: Store the notification policy (table and repository)

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §6
- **Assigned agent / harness / model:**
- **Depends on:** BE-025
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files + generated migration, ~12 min

## Goal

The policy is saved in one database row and loaded as the frozen `NotificationPolicy`, with defaults when the row does not exist.

## Why this ticket exists

`/pause` from Telegram and the settings screen both need to change the policy, so it cannot live in environment variables. One row, one getter, one saver.

## Read first

- `api/app/bills/models.py` and `repository.py`.
- `api/migrations/env.py`: register the new models module.

## Design

- **Pattern:** Repository; single-row table enforced by a CHECK constraint.
- **Data flow:** `get_policy(session)` → row or defaults → `NotificationPolicy`; `save_policy(session, policy)` → upsert.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/notifications/models.py` (new), `api/app/notifications/repository.py` (new).
- `api/migrations/env.py` (changed) and a generated revision `create notification_policy`.
- `api/tests/test_notification_repository.py` (new).

**Table `notification_policy`**

| Column | Type | Rules |
|---|---|---|
| `id` | `SmallInteger` | primary key; CHECK `id = 1` (exactly one row can exist) |
| `quiet_start`, `quiet_end` | `Time` | not null |
| `timezone` | `String(64)` | not null |
| `paused_until` | timestamptz | nullable |
| `urgent_categories` | `JSONB` | array of strings |
| `caps` | `JSONB` | object of string → int |
| `grouping_window_minutes` | `SmallInteger` | CHECK 0–120 |
| `updated_at` | timestamptz | server-managed |

**Functions**

- `async def get_policy(session) -> NotificationPolicy`: the row mapped to the model, or `NotificationPolicy()` (defaults) when there is no row. Never inserts.
- `async def save_policy(session, policy: NotificationPolicy) -> NotificationPolicy`: `INSERT … ON CONFLICT (id) DO UPDATE`; commits; returns what was stored.

## Steps

1. Model and migration.
2. `get_policy`.
3. `save_policy`.
4. Tests.

## Tests

- `test_get_policy_returns_defaults_when_empty`
- `test_save_then_get_round_trips_every_field`
- `test_saving_twice_keeps_one_row`
- `test_second_row_is_rejected_by_check`
- `test_paused_until_stays_timezone_aware`

## Acceptance criteria

- [ ] Exactly one policy row can exist
- [ ] With an empty table the defaults are 20:00–08:00 America/Mexico_City, not paused
- [ ] `downgrade` removes the table
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-migrate
```

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The CHECK that pins `id = 1`.
2. `get_policy` does not write.
3. The migration contains only this table.

Things that should *not* be in the diff: endpoints; Telegram code.

## Out of scope

- HTTP access → BE-027.
- `/pause` → BE-028.

## Notes / log

The agent adds progress notes, decisions and open questions here.
