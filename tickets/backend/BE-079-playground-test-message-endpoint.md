# BE-079: `POST /admin/telegram/test-message`: send a test to the owner's chat now

- **Status:** in review
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** BE-021, BE-068, BE-069, BE-077
- **Can run in parallel with:** BE-070, BE-071
- **Public endpoint?** no
- **Review size:** ~70 lines, 3 files plus tests, ~12 min

## Goal

An admin can send a chosen template as a real message to the allowlisted chat, immediately, at most 10 times per hour.

## Why this ticket exists

The only first-slice tool that reaches outside the app, so it is the most constrained: one fixed recipient, the normal sender, a hard hourly limit, and a record of every attempt.

Re-scoped on 2026-11-22: the outbox and notification policy moved to EPIC-010. A test message is something the admin just asked for, like a reply, so it goes through `service.reply` (BE-021) and is sent at once: no queue, no quiet hours.

## Read first

- `api/app/telegram/service.py` (BE-021): `reply`.
- `api/app/telegram/playground/repository.py` (BE-069): `record_action`, `count_actions_since`.
- `api/app/telegram/playground/router.py` (BE-078): `_render_or_http_error`, `TemplateRequest`.

## Design

- **Pattern:** Plain route with a pure limit check (`may_send`).
- **Data flow:** body → `count_actions_since("test_message", now − 1h)` → `may_send` → render check → `service.reply(sender, allowed_user_id, Reply(...))` → `200`; `record_action`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files:** `api/app/telegram/playground/router.py`, `schemas.py` (changed); `api/app/telegram/playground/limits.py` (new): `TEST_MESSAGES_PER_HOUR = 10`, `def may_send(sent_last_hour: int, limit: int = TEST_MESSAGES_PER_HOUR) -> bool` (pure).

**Request:** `{"template": "help", "data": {}}`, same schema and limits as BE-078 (`TemplateRequest`, unknown fields rejected). There is no recipient field.

**Responses**

| Case | Status | Body | Recorded as |
|---|---|---|---|
| Sent | `200` | `{"messageId": 123}` | `ok` |
| Limit reached | `429` | `{"detail": "Test message limit reached (10 per hour)"}` | `rejected` |
| Unknown template / missing field / too long | `404` / `422` | as BE-078 | `rejected` |
| Telegram not configured | `409` | detail names the missing setting, no value | `failed` |
| Telegram refused or unreachable | `502` | `{"detail": "Telegram refused the message (<ErrorType>)"}` | `failed` |

**Rules**

- `chat_id` is always `settings.telegram_allowed_user_id`.
- The limit is checked before anything is rendered or sent, and counts only `ok` sends in the last hour.
- Rejected and failed attempts are committed before the error is raised (the request session rolls back on error).
- Message text and template data are never stored or logged.

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
- `test_test_message_sends_to_allowed_chat_only`.
- `test_eleventh_in_an_hour_is_429_and_recorded_rejected`.
- `test_unconfigured_telegram_is_409`: no bot token, and no allowed user ID.
- `test_telegram_refusal_is_502_and_recorded_failed`.
- `test_unknown_template_is_404_and_sends_nothing`.
- `test_request_cannot_set_recipient`: an extra `chatId` field is rejected.

## Acceptance criteria

- [ ] A test message is sent through `service.reply` to the allowlisted chat only
- [ ] The eleventh attempt within an hour gets `429`, before anything is sent
- [ ] The four guard cases hold
- [ ] Every attempt is recorded (`ok`, `rejected` or `failed`)
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. With `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USER_ID` set in `api/.env`, as admin: POST `{"template": "help", "data": {}}` → `200`, and the message arrives in your chat. No webhook or tunnel is needed to send.

## Review guide

Read the diff in this order, and check:

1. Where does `chat_id` come from? Only settings.
2. Is the limit checked before `service.reply`?
3. Is a rejected or failed attempt still recorded?

Things that should *not* be in the diff: Free-text messages, other recipients, queues, policies.

## Out of scope

- The panel and confirmation → FE-029.
- Queued, policy-governed sends → EPIC-010.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- The template is rendered once up front only to map its errors to 404 / 422 before sending; `service.reply` renders it again to send. Cheap and pure, and it keeps `service.reply` the one send path.
- Telegram 429 (`RateLimited`) is a `502` like any other refusal; retrying is not this endpoint's job.
