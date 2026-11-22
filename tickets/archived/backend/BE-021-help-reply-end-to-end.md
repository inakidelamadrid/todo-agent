# BE-021: The bot replies: /help works end to end

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3, §8
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** BE-015, BE-019, BE-020
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~50 lines, 3 files, ~8 min

## Goal

When a handler returns a `Reply`, the webhook renders it and sends it to the chat. `/help` answers with the command list.

## Why this ticket exists

First visible behaviour: until now every piece was tested in isolation. This ticket joins them with a dozen lines and is the first one you can try from your phone.

## Read first

- `api/app/telegram/webhook.py`, `handlers.py`, `templates.py`, `sender.py`.

## Design

- **Pattern:** Facade: one `reply` function in the Telegram service hides render + send from the webhook.
- **Data flow:** handler → `Reply` → `service.reply(sender, chat_id, reply)` → `render` → `sender.send`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/service.py` (new).
- `api/app/telegram/webhook.py` (changed).
- `api/tests/test_telegram_reply.py` (new).

**Function**

```python
async def reply(sender: TelegramSender, chat_id: int, reply: Reply) -> SentMessage
```
Renders `reply.template` with `reply.data` and sends it. No buttons yet.

**Why replies skip the outbox.** A reply answers something you just sent, so quiet hours, caps and grouping do not apply to it: it goes out immediately. Messages the app *initiates* (reminders, digests) go through `service.send` and the policy (BE-030). Both live in `service.py`, so "all outbound goes through the Telegram service" (epic §8) holds.

**Webhook.** After the handler returns a `Reply` and `update.chat_id` is known: `await service.reply(sender, update.chat_id, reply)`. A `SendFailed` is caught: mark the update `failed`, log `telegram.reply_failed`, still return `200`. The sender comes from `Depends(get_sender)`.

## Steps

1. Write `service.reply`.
2. Call it from the webhook; handle `SendFailed`.
3. Tests with the recording fake (override `get_sender`).

## Tests

- `test_help_command_sends_help_text_to_the_same_chat`
- `test_unknown_command_reply_names_the_command`
- `test_no_reply_sends_nothing`: a handler returning `None`.
- `test_send_failure_marks_update_failed_and_returns_200`
- `test_stranger_gets_no_reply`
- `test_duplicate_update_gets_one_reply`

## Acceptance criteria

- [ ] `/help` from the owner produces exactly one message containing the command list
- [ ] A stranger or a duplicate delivery produces no message
- [ ] A send failure never causes a non-200 response to Telegram
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

After BE-039 and BE-040 (dev bot and tunnel): send `/help` to the dev bot and read the reply. Send it from a second account: nothing comes back.

## Review guide

Read the diff in this order, and check:

1. `service.reply`: two lines of work.
2. `webhook.py`: the reply is sent after the handler and before `mark_update`; the failure branch.
3. The duplicate test: this is the proof that idempotency protects outbound too.

Things that should *not* be in the diff: queueing, policy, buttons.

## Out of scope

- Policy-governed sends → BE-030.
- Buttons → BE-023.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Fixed BE-015's `_unknown_command`: it now passes `{"command": update.command}`, otherwise `render` raised `MissingTemplateData`.
- The webhook catches any exception from the reply, not only `SendFailed`: a render bug or a validation error must not turn into a non-200. The log line is `telegram.reply_failed <TypeName>` only (a validation error's message would carry the text).
- `telegram_webhook_client` now overrides `get_sender` with the recording fake (`recorded_sends` fixture) and empties `TELEGRAM_BOT_TOKEN`, so no webhook test can reach Telegram even with a real token in `api/.env`.
