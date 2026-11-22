# BE-071: `GET /admin/telegram/updates`: the update log

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-068, BE-069, BE-070
- **Can run in parallel with:** BE-072, BE-073, BE-077
- **Public endpoint?** no
- **Review size:** ~50 lines, 2 files plus tests, ~10 min

## Goal

An admin can list recent updates as metadata: kind, route, status, time, and whether the playground made it.

## Why this ticket exists

The first playground tool and the simplest: read only. It shows what the bot received and what it decided, which answers most 'why did nothing happen?' questions.

## Read first

- `api/app/telegram/playground/router.py` (BE-068).
- `api/app/bills/router.py` and `schemas.py`: response models in camelCase.
- `list_recent_updates` (BE-070).

## Design

- **Pattern:** Plain route: validate query → repository → response model.
- **Data flow:** `GET /admin/telegram/updates?limit=&status=&route=` → `list_recent_updates` → `UpdateLogResponse`; then `record_action(…, "updates", "ok")`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/playground/schemas.py` (new or changed): camelCase, frozen.
- `api/app/telegram/playground/router.py` (changed).

**Request:** `limit` (1–200, default 50), `status` (`received` | `processed` | `failed`, optional), `route` (≤ 40 chars, optional). Invalid values → `422`.

**Response `200`**

```json
{"items": [
  {"updateId": 812345, "kind": "command", "route": "core.help", "status": "processed",
   "receivedAt": "2026-11-16T15:04:05Z", "playground": false}
]}
```

- `playground` is true when `updateId` is negative (replays, BE-076).
- No chat ID, message ID, text or caption is returned. The epic's 'latency' is not stored in `telegram_updates`, so it is not shown; say so in the Notes if you find an easy source.

## Steps

1. Schemas.
2. Route.
3. Tests with the fake decoder and the integration database.
4. Run `make api-test`.

## Tests

- `test_updates_without_credentials_returns_401`: no credentials → `401`.
- `test_updates_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_updates_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_updates_when_playground_off_returns_404`: playground switched off → `404`.
- `test_updates_returns_metadata_newest_first`.
- `test_updates_filters_and_validates_query`: bad `status` → `422`.
- `test_negative_update_id_is_marked_playground`.
- `test_response_has_no_chat_or_message_ids`.
- `test_listing_records_an_action`.

## Acceptance criteria

- [ ] An admin gets recent updates as camelCase metadata, newest first
- [ ] The four guard cases answer `401`, `403`, `403`, `404`
- [ ] No chat ID, message ID or content is in the response
- [ ] Each call records a `updates` action
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. With the playground on and after sending the dev bot a message: signed in as admin, `fetch('/api/admin/telegram/updates', …)` from the console lists it.

## Review guide

Read the diff in this order, and check:

1. `schemas.py`: which fields leave the server? Only the six above.
2. `router.py`: is the route on `playground_router`?

Things that should *not* be in the diff: Deleting or editing updates, message content, pagination cursors.

## Out of scope

- The panel → FE-023, FE-024.

## Notes / log

The agent adds progress notes, decisions and open questions here.
