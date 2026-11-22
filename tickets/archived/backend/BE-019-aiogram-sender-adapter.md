# BE-019: aiogram Bot adapter for the sender port

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** BE-004, BE-005, BE-018
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~12 min

## Goal

A real `TelegramSender` backed by aiogram's `Bot` is created at startup when a token is configured.

## Why this ticket exists

This is the only file that performs Telegram HTTP calls. Keeping it apart from the port means the reviewer can check the translation to aiogram (and the error mapping) without reading any business logic.

## Read first

- Confirm every aiogram name used here against https://docs.aiogram.dev/ (v3) before coding; do not rely on memory.
- `api/app/main.py` lifespan: where long-lived clients are created and closed.
- `api/app/telegram/sender.py` from BE-018.

## Design

- **Pattern:** Adapter: a factory function closes over a `Bot` and returns the port.
- **Data flow:** lifespan → `Bot(token)` → `aiogram_sender(bot)` → `app.state.telegram_sender` → `get_sender` dependency.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `aiogram` | installed (BE-005) | `Bot` HTTP client | Already chosen; handles Telegram's request and response format, including the 429 `retry_after` value. |

## Details

**Files**

- `api/app/telegram/aiogram_sender.py` (new).
- `api/app/main.py` (changed): lifespan creates the bot when `telegram_bot_token` is set, and closes its session on shutdown.
- `api/tests/test_telegram_aiogram_sender.py` (new).

**Functions**

- `aiogram_sender(bot: Bot) -> TelegramSender`
  - `send` → `bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=…)`. Button rows map to an `InlineKeyboardMarkup`; no buttons → no markup. Link previews disabled.
  - `edit` → `bot.edit_message_text(...)`, `parse_mode="HTML"`.
  - `delete` → `bot.delete_message(...)`.
  - `answer_callback` → `bot.answer_callback_query(callback_id, text or None)`.
- Error mapping, in one small helper used by all four:
  - aiogram's retry-after exception → `RateLimited(retry_after=…)`;
  - any other aiogram API or network exception → `SendFailed` (message is the exception type name only, never the request).
- `unconfigured_sender() -> TelegramSender`: every operation raises `TelegramNotConfigured`. Used when the token is empty, so the app still starts.
- `get_sender(request: Request) -> TelegramSender`: returns `request.app.state.telegram_sender`.

**Tests** use `unittest.mock.AsyncMock(spec=Bot)`. No test touches the network.

## Steps

1. Write `aiogram_sender` operation by operation, each with a mock-based test.
2. Add the error mapping.
3. Add `unconfigured_sender`, the dependency and the lifespan wiring.

## Tests

- `test_send_passes_text_html_and_no_markup_without_buttons`
- `test_send_builds_inline_keyboard_rows`
- `test_send_returns_message_id`
- `test_edit_delete_answer_call_the_bot`
- `test_retry_after_maps_to_rate_limited_with_seconds`
- `test_other_api_error_maps_to_send_failed`
- `test_unconfigured_sender_raises_not_configured`
- `test_app_starts_without_token`

## Acceptance criteria

- [ ] `aiogram_sender.py` is the only module under `api/app/` that imports `aiogram.Bot`
- [ ] The bot's HTTP session is closed on shutdown
- [ ] No test performs a network call
- [ ] The bot token never appears in an exception message or log
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

A real message is first sent in BE-021 once the dev bot exists (BE-040).

## Review guide

Read the diff in this order, and check:

1. The four operations: each is a one-to-one translation.
2. The error helper: does any path leak the token or message text into the exception?
3. `main.py`: created once, closed once.

Things that should *not* be in the diff: queueing, retries, policy checks, templates.

## Out of scope

- Retrying after `RateLimited` → BE-032.
- Downloading files → BE-035.
- Webhook registration → BE-039.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Stacked on BE-018 (not yet merged when this was built); merge BE-018 first.
- aiogram names checked against the installed 3.32.0: `TelegramRetryAfter.retry_after`, `AiogramError` (base of API and network errors), `LinkPreviewOptions(is_disabled=True)`.
- Added `open_sender(token)`, an async context manager, so `main.py` never imports `aiogram.Bot` and closing the session lives next to creating it. Extra test: `test_open_sender_closes_bot_session`.
- Errors are raised `from None`: the aiogram exception (whose request carries the message text) is not chained.
