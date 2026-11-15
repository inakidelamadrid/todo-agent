# BE-012: Webhook processes each update once

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-009, BE-011
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~40 lines, 2 files, ~8 min

## Goal

A repeated delivery of the same `update_id` returns `200` and does nothing.

## Why this ticket exists

This connects the claim from BE-011 to the route. It is a few lines, but they are the lines that guarantee "exactly once", so they get their own review.

## Read first

- `api/app/telegram/webhook.py` as left by BE-009.
- `api/app/db.py`: the `get_session` dependency.

## Design

- **Pattern:** Idempotency key, enforced at the edge before any work happens.
- **Data flow:** guard → parse → allowlist → `claim_update` → duplicate: `200`; new: (dispatch arrives in BE-015) → `mark_update(processed)` → `200`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/webhook.py` (changed).
- `api/tests/test_telegram_webhook.py` (changed).

**Behaviour**

- The route gains `session: Annotated[AsyncSession, Depends(get_session)]`.
- After the allowlist: `if not await repository.claim_update(session, update): return ack`.
- For a new update: `await repository.mark_update(session, update.update_id, "processed")`, then the ack. (BE-015 inserts dispatch between the two.)
- Order matters and must stay: secret → parse → allowlist → claim. Strangers never reach the database.

## Steps

1. Add the session dependency and the claim.
2. Mark as processed.
3. Add the tests.

## Tests

- `test_same_update_twice_stores_one_row`
- `test_second_delivery_returns_200`
- `test_stranger_update_is_not_stored`
- `test_new_update_is_marked_processed`

## Acceptance criteria

- [ ] Posting one fixture twice leaves one row in `telegram_updates`
- [ ] Both deliveries return `200`
- [ ] A stranger's update leaves no row
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Post `text.json` twice with curl (as in BE-008), then in `make db-psql`: `select update_id, status from telegram_updates;` shows one row.

## Review guide

Read the diff in this order, and check:

1. The order of the four steps in the route.
2. The duplicate branch returns before anything else runs.

Things that should *not* be in the diff: routing, handlers, replies.

## Out of scope

- Deciding where the update goes → BE-013.
- Running a handler → BE-015.

## Notes / log

The agent adds progress notes, decisions and open questions here.
