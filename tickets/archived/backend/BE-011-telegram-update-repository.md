# BE-011: Repository: claim an update once, mark its outcome

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2
- **Assigned agent / harness / model:**
- **Depends on:** BE-006, BE-010
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files, ~10 min

## Goal

`claim_update` records an update and tells the caller whether this is the first time it has been seen; `mark_update` records how it ended.

## Why this ticket exists

"Have we seen this?" and "remember it" must be one atomic database statement. Two separate steps (select, then insert) would let two simultaneous retries both pass the check. This ticket isolates that one statement.

## Read first

- `api/app/bills/repository.py`: `upsert_payment` uses the same PostgreSQL `INSERT … ON CONFLICT` construct.
- https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert

## Design

- **Pattern:** Repository as a module of functions; insert-or-ignore as the atomic claim.
- **Data flow:** `InboundUpdate` → `claim_update(session, update)` → `True` (new) / `False` (duplicate).

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/repository.py` (new).
- `api/tests/test_telegram_repository.py` (new, uses the integration database fixtures in `conftest.py`).

**Functions**

```python
async def claim_update(session: AsyncSession, update: InboundUpdate) -> bool
```
`INSERT INTO telegram_updates (update_id, chat_id, message_id, kind) … ON CONFLICT (update_id) DO NOTHING RETURNING update_id`. Returns `True` when a row came back. Commits.

```python
async def mark_update(session: AsyncSession, update_id: int, status: str, route: str = "") -> None
```
Sets `status` (`processed` or `failed`) and `route`. Commits. Unknown `update_id` is a no-op.

```python
async def delete_updates_before(session: AsyncSession, cutoff: datetime) -> int
```
Deletes rows with `received_at < cutoff`; returns the count. Nothing calls it yet; the daily clean-up job (BE-055) will, with a 30-day cutoff.

## Steps

1. Write `claim_update` and its two tests.
2. Write `mark_update`.
3. Write `delete_updates_before`.

## Tests

- `test_first_claim_returns_true_and_stores_row`
- `test_second_claim_returns_false_and_keeps_one_row`
- `test_concurrent_claims_yield_exactly_one_true`: two sessions with `asyncio.gather`.
- `test_mark_update_sets_status_and_route`
- `test_mark_unknown_update_is_noop`
- `test_delete_updates_before_removes_only_older_rows`

## Acceptance criteria

- [ ] Claiming is a single statement using `ON CONFLICT DO NOTHING`
- [ ] Concurrent claims of one `update_id` yield exactly one `True`
- [ ] The module has no FastAPI imports
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make db-up
```

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `claim_update`: one statement, no prior `SELECT`.
2. The concurrency test: do you believe it would fail with a select-then-insert implementation?

Things that should *not* be in the diff: webhook changes; a scheduler.

## Out of scope

- Calling it from the webhook → BE-012.
- Scheduling the cleanup → BE-055.

## Assumptions

- Updates are kept 30 days (the epic says "N days"). Telegram stops retrying within about a day, so any value above that is safe.

## Notes / log

The agent adds progress notes, decisions and open questions here.
