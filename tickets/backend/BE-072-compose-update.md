# BE-072: Compose an update: a small form becomes an `InboundUpdate`

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-006
- **Can run in parallel with:** BE-065 to BE-071
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files plus tests, ~10 min

## Goal

`compose_update(composed, user_id, update_id)` turns a small validated description (kind, text or caption) into the same `InboundUpdate` the webhook would build, always from the owner's own chat.

## Why this ticket exists

The explainer and the replay need an update to work on, and it must be parsed exactly like a real one. Building a minimal Telegram payload and passing it through the existing `to_inbound` guarantees that, instead of constructing `InboundUpdate` by hand and drifting from the real parser.

## Read first

- `api/app/telegram/inbound.py` (BE-006): `to_inbound` and `InboundUpdate`.
- `api/tests/fixtures/` (BE-005): what real payloads look like.

## Design

- **Pattern:** Pure mapping that reuses the real parser (one source of truth for parsing).
- **Data flow:** `ComposedUpdate` → minimal Telegram update dict → aiogram `Update` → `to_inbound` → `InboundUpdate`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/playground/schemas.py` (new or changed):

```python
class ComposedUpdate(BaseModel):            # frozen, camelCase aliases
    kind: Literal["text", "command", "photo", "document", "voice"]
    text: str = ""                           # text and command: 1-4096 chars; a command must start with "/"
    caption: str = ""                        # photo and document: 0-1024 chars
```
  Validation: `text` required for `text` and `command`; `command` must start with `/`; `caption` only for `photo` and `document`. Violations → `ValueError` → `422`.

- `api/app/telegram/playground/compose.py` (new):

```python
def compose_update(composed: ComposedUpdate, *, user_id: int, update_id: int) -> InboundUpdate   # pure
SAMPLES: Mapping[str, ComposedUpdate]    # immutable: "help-command", "plain-text", "photo-with-vault-caption", "unknown-command"
```
  The payload always uses `user_id` for both the sender and the chat (a private chat with the owner), a fixed dummy `message_id`, and a placeholder `file_id` for media kinds. There is no way to set another sender.

Callback taps are not composable here: their data must be signed (BE-022, BE-023). They come with the callback decoder tool, later.

## Steps

1. Schemas with validation.
2. `compose_update` through `to_inbound`.
3. Samples.
4. Run `make api-test`.

## Tests

- `test_text_becomes_text_update_from_owner_chat`.
- `test_slash_text_becomes_command_with_args`: `/help me` → `command='help'`, `command_args='me'`.
- `test_photo_carries_caption`.
- `test_sender_and_chat_are_always_the_given_user`.
- `test_command_without_slash_is_rejected`; `test_empty_text_is_rejected`; `test_caption_on_text_is_rejected`.
- `test_every_sample_composes`.

## Acceptance criteria

- [ ] `compose_update` is pure and goes through `to_inbound`
- [ ] The sender and chat are always the given user ID
- [ ] Invalid combinations are rejected by the schema
- [ ] Four samples exist and all compose
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_playground_compose.py -q`: green.

## Review guide

Read the diff in this order, and check:

1. `compose.py`: does it call `to_inbound` instead of building `InboundUpdate` directly?
2. `schemas.py`: can any field choose the sender? It must not.

Things that should *not* be in the diff: Routes, callbacks, real file IDs.

## Out of scope

- Explaining the route → BE-073, BE-074.
- Running it for real → BE-076.

## Notes / log

The agent adds progress notes, decisions and open questions here.
