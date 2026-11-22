# FE-022: Playground client, part 2: send test message

- **Status:** done
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** FE-021, BE-079
- **Can run in parallel with:** FE-023 to FE-028
- **Review size:** ~35 lines, 2 files plus tests, ~6 min

## Goal

A typed client function sends a test message: a template and its data, never a recipient.

## Why this ticket exists

Kept apart from the read-only client so the reviewer sees the one call that reaches Telegram on its own. Re-scoped on 2026-11-22: explain and replay moved to FE-030 (EPIC-011), and BE-079 now sends immediately instead of queueing.

## Read first

- `web/src/features/playground/api.ts` and `types.ts` (FE-021).
- The request and response shapes in BE-079.

## Design

- **Pattern:** One typed client function; no recipient parameter exists.
- **Data flow:** `sendTestMessage(template, data)` → `POST /admin/telegram/test-message` → `TestMessageResult`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/types.ts` (changed): `TestMessageResult { messageId: number }`.
- `web/src/features/playground/api.ts` (changed): `sendTestMessage(template: string, data: Readonly<Record<string, string>>): Promise<TestMessageResult>`.

Errors surface as the existing API error with the server's `detail`: `429` (hourly limit), `409` (Telegram not configured), `502` (Telegram refused), `404` / `422` (template or field).

## Steps

1. Type and client function with tests.
2. `make web-test`, `make web-build`.

## Tests

- `test_send_test_message_posts_template_and_data_without_recipient`.
- `test_send_test_message_returns_message_id`.
- `test_429_409_502_surface_as_api_error_with_detail`.

## Acceptance criteria

- [ ] `sendTestMessage` is typed and tested
- [ ] No client function accepts a recipient
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-test` and `make web-build`: green.

## Review guide

Read the diff in this order, and check:

1. The request body: only `template` and `data`.

Things that should *not* be in the diff: UI, stores, explain or replay (FE-030).

## Out of scope

- Wiring → FE-029.
- Explain and replay → FE-030.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `sendTestMessage(template, data)` posts only `{ template, data }` and returns `{ messageId }`; no function takes a recipient.
- First built against the old queued contract; re-done after BE-079 was re-scoped. Explain/replay code from that first pass was taken out of this branch (FE-030 can reuse it).
