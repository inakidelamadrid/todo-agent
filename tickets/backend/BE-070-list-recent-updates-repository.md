# BE-070: Repository: list recent Telegram updates with filters

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-011
- **Can run in parallel with:** BE-065 to BE-069
- **Public endpoint?** no
- **Review size:** ~40 lines, 1 file plus tests, ~8 min

## Goal

`list_recent_updates(session, limit, status, route)` returns the newest `telegram_updates` rows, optionally filtered.

## Why this ticket exists

The update log tool needs one read query. It belongs with the other Telegram repository functions and is tested against the real database before any route exists.

## Read first

- `api/app/telegram/repository.py` (BE-011): `claim_update`, `mark_update`.
- `api/app/telegram/models.py` (BE-010): the columns.
- `api/app/bills/repository.py`: a list query.

## Design

- **Pattern:** Repository function; read only.
- **Data flow:** `list_recent_updates` → `SELECT … ORDER BY received_at DESC, update_id DESC LIMIT n`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/telegram/repository.py` (changed).

```python
async def list_recent_updates(
    session: AsyncSession, *, limit: int = 50,
    status: str | None = None, route: str | None = None,
) -> Sequence[TelegramUpdate]
```

- `limit` is clamped to 1–200 inside the function.
- `status` filters by exact value; `route` by exact `route` value. Both optional, combined with AND.
- Newest first. No message content exists in the table, so none can be returned.

## Steps

1. Write the tests with a few inserted rows.
2. Write the query.
3. Run `make api-test`.

## Tests

- `test_returns_newest_first`.
- `test_limit_is_clamped`: 0 → 1, 999 → 200.
- `test_filters_by_status`.
- `test_filters_by_route`.
- `test_filters_combine`.
- `test_empty_table_returns_empty_list`.

## Acceptance criteria

- [ ] The function returns rows newest first with the limit clamped to 1–200
- [ ] Status and route filters work alone and together
- [ ] It performs no write
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_telegram_repository.py -q`: green.

## Review guide

Read the diff in this order, and check:

1. The query: is the ordering stable (tie-break on `update_id`)?
2. Is the limit clamped in one place?

Things that should *not* be in the diff: A route, pagination cursors, counts.

## Out of scope

- The endpoint → BE-071.

## Notes / log

The agent adds progress notes, decisions and open questions here.
