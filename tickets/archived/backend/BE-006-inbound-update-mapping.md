# BE-006: Map aiogram's Update to our own InboundUpdate

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2
- **Assigned agent / harness / model:**
- **Depends on:** BE-005
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 2 files, ~12 min

## Goal

One pure function turns any Telegram `Update` into a small frozen `InboundUpdate` holding only the fields the app uses.

## Why this ticket exists

aiogram's `Update` has hundreds of optional fields. If the router, allowlist and handlers read it directly, Telegram's vocabulary spreads through the codebase. This mapping is the only place that knows Telegram's shape; everything after it works with twelve plain fields.

## Read first

- `api/app/bills/schemas.py`: frozen Pydantic models, the house style.
- `api/tests/fixtures/telegram/*.json` from BE-005.
- Confirm every aiogram name used here against https://docs.aiogram.dev/ (v3) before coding; do not rely on memory.

## Design

- **Pattern:** Anti-corruption layer: one mapping function at the edge, and nothing past it sees the foreign type.
- **Data flow:** `Update` → `to_inbound(update)` → `InboundUpdate`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/__init__.py` (new, empty).
- `api/app/telegram/inbound.py` (new).
- `api/tests/test_telegram_inbound.py` (new).

**Types**

```python
class UpdateKind(StrEnum):
    TEXT = "text"; COMMAND = "command"; VOICE = "voice"; PHOTO = "photo"
    DOCUMENT = "document"; CALLBACK = "callback"; UNSUPPORTED = "unsupported"

class InboundUpdate(BaseModel):          # frozen
    update_id: int
    kind: UpdateKind
    user_id: int | None = None           # who sent it
    chat_id: int | None = None
    message_id: int | None = None
    text: str | None = None              # message text, TEXT and COMMAND only
    command: str | None = None           # "help" for "/help" or "/help@my_bot"; lower-case
    command_args: str = ""               # the rest of the line, trimmed
    caption: str | None = None           # PHOTO and DOCUMENT
    file_id: str | None = None           # VOICE, PHOTO (largest size), DOCUMENT
    file_size: int | None = None
    mime_type: str | None = None         # photos are "image/jpeg"
    callback_id: str | None = None       # CALLBACK
    callback_data: str | None = None     # CALLBACK
```

**Functions (both pure)**

- `to_inbound(update: Update) -> InboundUpdate`
  - `callback_query` present → `CALLBACK`; `user_id` from `callback_query.from_user`, `chat_id` and `message_id` from its `message` when present.
  - `message.text` starting with `/` → `COMMAND`. Otherwise `message.text` → `TEXT`.
  - `message.voice` → `VOICE`; `message.photo` → `PHOTO` using the **last** (largest) size; `message.document` → `DOCUMENT`.
  - Anything else (stickers, edited messages, channel posts, …) → `UNSUPPORTED` with only `update_id` and whatever IDs exist.
- `source_ref(update: InboundUpdate) -> str | None`: `"telegram:<chat_id>:<message_id>"`, or `None` when either is missing. Downstream records use it to trace their origin (epic §5.2).

## Steps

1. Create the package and the two types.
2. Write `to_inbound` one branch at a time, each with its fixture test.
3. Add `source_ref`.

## Tests

- `test_text_message_maps_to_text`
- `test_command_strips_slash_and_bot_suffix`: `/Help@my_bot now` → `command == "help"`, `command_args == "now"`.
- `test_voice_carries_file_id_size_and_mime`
- `test_photo_uses_largest_size_and_keeps_caption`
- `test_document_carries_mime_type`
- `test_callback_carries_id_data_and_origin_message`
- `test_unknown_update_is_unsupported`: an update with only `edited_message`.
- `test_source_ref_format`, `test_source_ref_is_none_without_message`
- `test_inbound_update_is_frozen`: assigning a field raises.

## Acceptance criteria

- [ ] `to_inbound` handles all seven fixtures as specified
- [ ] `InboundUpdate` is frozen
- [ ] `inbound.py` is the only file under `api/app/` that imports `aiogram.types.Update`
- [ ] `to_inbound` and `source_ref` perform no I/O
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `InboundUpdate`: do you understand what each of the fields is for? Anything unused should go.
2. `to_inbound`: one branch per kind, in the order above; no branch reaches for a field without checking it exists.
3. Tests: one per branch.

Things that should *not* be in the diff: routes, database code, logging, any decision about what to *do* with an update.

## Out of scope

- Checking who sent it → BE-009.
- Deciding where it goes → BE-013.

## Notes / log

The agent adds progress notes, decisions and open questions here.
