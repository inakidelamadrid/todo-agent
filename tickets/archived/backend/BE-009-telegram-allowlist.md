# BE-009: Allowlist: only the owner's updates are processed

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-008
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~50 lines, 3 files, ~8 min

## Goal

Updates from anyone other than the configured Telegram user are dropped with a `200`, no reply, and one counter log line.

## Why this ticket exists

Anyone on Telegram can message the bot, and Telegram will faithfully deliver it with the correct secret. The secret proves the request is from Telegram; the allowlist proves it is from you. They are separate checks and this ticket adds the second.

## Read first

- `api/app/bills/domain.py`: a pure predicate (`is_due_in_month`).
- In a private chat, Telegram's `chat.id` equals the user's `id`. The bot is private-only, so both must equal the allowed ID.

## Design

- **Pattern:** Specification / predicate: one named pure function holds the rule; the route only calls it.
- **Data flow:** `InboundUpdate` → `is_allowed(update, settings.telegram_allowed_user_id)` → false: log and `200`; true: continue.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/allowlist.py` (new).
- `api/app/telegram/webhook.py` (changed).
- `api/tests/test_telegram_allowlist.py` (new).

**Function (pure)**

```python
def is_allowed(update: InboundUpdate, allowed_user_id: int | None) -> bool
```

True only when all hold:

- `allowed_user_id is not None` (unconfigured → nobody is allowed);
- `update.user_id == allowed_user_id`;
- `update.chat_id is None or update.chat_id == allowed_user_id` (rejects groups the owner might be in).

**Route.** After parsing: if not allowed, `logger.info("telegram.ignored")` and return the ack. The log line carries **no** user ID, chat ID or text. No reply is sent, so a stranger cannot tell the bot exists.

## Steps

1. Write the predicate with its tests.
2. Call it in the route.
3. Add the route-level tests.

## Tests

- `test_owner_is_allowed`
- `test_stranger_is_not_allowed`
- `test_owner_in_another_chat_is_not_allowed`: `user_id` matches, `chat_id` differs.
- `test_nobody_is_allowed_when_unconfigured`
- `test_update_without_user_is_not_allowed`
- `test_webhook_drops_stranger_with_200_and_logs_counter`: uses `stranger_text.json` and `caplog`; the record has no `999999` in it.

## Acceptance criteria

- [ ] A stranger's update returns `200 {"ok": true}` and triggers nothing else
- [ ] With `TELEGRAM_ALLOWED_USER_ID` unset every update is dropped
- [ ] The ignored log line contains no IDs or message content
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `allowlist.py`: three conditions, no I/O.
2. `webhook.py`: the check comes before anything that will later touch the database.
3. The log line: nothing identifying in it.

Things that should *not* be in the diff: storing ignored updates (a stranger could fill the table); replying to strangers.

## Out of scope

- Pairing by `/start <code>` instead of an environment variable → BE-046 (deferred).
- Structured logging → BE-042.

## Assumptions

- The allowed ID is read from `TELEGRAM_ALLOWED_USER_ID` until pairing (BE-046) is designed. If pairing lands, only the second argument of `is_allowed` changes source.

## Notes / log

The agent adds progress notes, decisions and open questions here.
