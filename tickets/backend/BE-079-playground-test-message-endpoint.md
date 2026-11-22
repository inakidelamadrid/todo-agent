# BE-079: `POST /admin/telegram/test-message`: send a test to the owner's chat

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-030, BE-068, BE-069
- **Can run in parallel with:** BE-071 to BE-078
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files plus tests, ~12 min

## Goal

An admin can queue a chosen template as a real message to the allowlisted chat, through `service.send`, at most 10 times per hour.

## Why this ticket exists

The only first-slice tool that reaches outside the app, so it is the most constrained: one fixed recipient, the normal sender with its policy, a hard hourly limit, and a record of every attempt.

## Read first

- `api/app/telegram/service.py` (BE-030): `send` and what it returns.
- `api/app/telegram/playground/repository.py` (BE-069): `count_actions_since`.
- `api/app/telegram/playground/router.py`.

## Design

- **Pattern:** Plain route with a pure limit check (`may_send`).
- **Data flow:** body → `count_actions_since("test_message", now − 1h)` → `may_send` → `service.send(chat_id=allowed_user_id, category="playground", …)` → `202`; `record_action`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files:** `api/app/telegram/playground/router.py`, `schemas.py` (changed); `api/app/telegram/playground/limits.py` (new): `TEST_MESSAGES_PER_HOUR = 10`, `def may_send(sent_last_hour: int, limit: int = TEST_MESSAGES_PER_HOUR) -> bool` (pure).

**Request:** `{"template": "help", "data": {}}`, same limits as BE-078. There is no recipient field.

**Responses**

| Case | Status | Body |
|---|---|---|
| Queued or deferred | `202` | `{"outboundId": "…", "status": "queued", "scheduledFor": "2026-11-16T15:04:05Z"}` |
| Limit reached | `429` | `{"detail": "Test message limit reached (10 per hour)"}`, recorded as `rejected` |
| Unknown template / missing field | `404` / `422` | as BE-078 |
| Telegram not configured | `409` | detail names the missing setting, no value |

**Rules**

- `chat_id` is always `settings.telegram_allowed_user_id`.
- `category="playground"`, `idempotency_key=f"playground:test:{action_id}"` (the ID from `record_action`, so each click is its own message).
- The notification policy applies: during quiet hours (20:00 to 08:00 by default) the answer is `status: "deferred"` with the time it will go out. The UI shows that; it is not an error.
- The message is delivered by the outbound worker (BE-031). Until that exists, the row is queued and nothing arrives.

## Steps

1. `may_send` and tests.
2. The route.
3. Tests.
4. Run `make api-test`.

## Tests

- `test_test_message_without_credentials_returns_401`: no credentials → `401`.
- `test_test_message_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_test_message_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_test_message_when_playground_off_returns_404`: playground switched off → `404`.
- `test_may_send_boundary`: 9 → true, 10 → false.
- `test_test_message_queues_to_allowed_chat_only`.
- `test_eleventh_in_an_hour_is_429_and_recorded_rejected`.
- `test_deferred_during_quiet_hours_reports_scheduled_time`.
- `test_unconfigured_telegram_is_409`.
- `test_request_cannot_set_recipient`: an extra `chatId` field is rejected or ignored.

## Acceptance criteria

- [ ] A test message is queued through `service.send` to the allowlisted chat only
- [ ] The eleventh attempt within an hour gets `429`
- [ ] Quiet hours produce `deferred` with the scheduled time, not an error
- [ ] The four guard cases hold
- [ ] Every attempt is recorded (`ok`, `rejected` or `failed`)
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. With the dev bot and the worker running, as admin: POST `{template: 'help', data: {}}` → `202`, and the message arrives (or is reported `deferred` at night).

## Review guide

Read the diff in this order, and check:

1. Where does `chat_id` come from? Only settings.
2. Is the limit checked before `service.send`?
3. Is a rejected attempt still recorded?

Things that should *not* be in the diff: Free-text messages, other recipients, bypassing the policy.

## Out of scope

- The panel and confirmation → FE-029.
- Delivery → BE-031.

## Notes / log

The agent adds progress notes, decisions and open questions here.
