# BE-018: Sender port and a recording fake

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** none
- **Can run in parallel with:** BE-004 to BE-017
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files, ~8 min

## Goal

The app has one agreed shape for "send, edit, delete a Telegram message", plus a fake that records calls for tests.

## Why this ticket exists

Everything outbound will call this port, never aiogram directly. Defining it before the real client means templates, the service and the webhook reply can all be built and tested with no network, and the reviewer sees the whole outbound surface in about thirty lines.

## Read first

- `api/app/telegram/sessions.py` (BE-016), if merged: the same "frozen dataclass of functions" port style. If not merged yet, this ticket introduces the style.
- Bot API methods we will need: `sendMessage`, `editMessageText`, `deleteMessage`, `answerCallbackQuery` (https://core.telegram.org/bots/api#available-methods).

## Design

- **Pattern:** Port + fake. The port is a frozen dataclass whose fields are async functions.
- **Data flow:** feature → `OutgoingMessage` → `sender.send(...)` → `SentMessage`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/sender.py` (new).
- `api/tests/fakes.py` (new): `recording_sender()`.
- `api/tests/test_telegram_sender_port.py` (new).

**Types (all frozen)**

```python
class Button(BaseModel):
    text: str                 # 1-40 chars
    callback_data: str        # 1-64 bytes (Telegram's limit)

class OutgoingMessage(BaseModel):
    chat_id: int
    text: str                 # 1-4096 chars, already rendered and escaped HTML
    buttons: tuple[tuple[Button, ...], ...] = ()    # rows of buttons

class SentMessage(BaseModel):
    message_id: int

@dataclass(frozen=True)
class TelegramSender:
    send: Callable[[OutgoingMessage], Awaitable[SentMessage]]
    edit: Callable[[int, int, str], Awaitable[None]]            # chat_id, message_id, new text
    delete: Callable[[int, int], Awaitable[None]]               # chat_id, message_id
    answer_callback: Callable[[str, str], Awaitable[None]]      # callback_id, short notice ("" for none)
```

**Errors** (plain exception types, defined here so callers never import aiogram's):

- `class SendFailed(Exception)`
- `class RateLimited(SendFailed)`, with `retry_after: float`
- `class TelegramNotConfigured(SendFailed)`

**Fake.** `recording_sender() -> tuple[TelegramSender, list[tuple[str, tuple]]]`: every call appends `(operation, args)`; `send` returns increasing message IDs from 1.

## Steps

1. Define the value types with their limits.
2. Define the port and the errors.
3. Write the fake and its tests.

## Tests

- `test_outgoing_message_rejects_empty_and_overlong_text`
- `test_button_rejects_callback_data_over_64_bytes`: counts bytes, not characters.
- `test_recording_sender_records_send_edit_delete_answer`
- `test_types_are_frozen`

## Acceptance criteria

- [ ] `sender.py` imports nothing from aiogram
- [ ] The 64-byte and 4096-character limits are enforced by the models
- [ ] The fake lives under `api/tests/`, not `api/app/`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The four operations on `TelegramSender`: is anything missing for the epic's §5.3, or present without a use?
2. The limits on `Button` and `OutgoingMessage`.

Things that should *not* be in the diff: aiogram imports, HTTP calls, policy or queue logic.

## Out of scope

- The real implementation → BE-019.
- Rendering text → BE-020.
- Signed callback data → BE-022.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `answer_callback` passes `""` for "no notice"; the adapter (BE-019) turns it into `None`.
- `RateLimited.__init__` takes `retry_after` positionally or by keyword; the message holds only the seconds.
