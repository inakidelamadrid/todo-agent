# BE-045: Ask "Keep this file?" after media is processed

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Media, §7, open question 7
- **Assigned agent / harness / model:**
- **Depends on:** BE-017, BE-023, BE-035
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~110 lines, 4 files, ~15 min

## Goal

After any voice note, photo or document is processed, the bot asks whether to keep the file, and a file is retained only after an explicit Keep.

## Why this ticket exists

You answered question 7 with "ask whether to keep, always". The safe way to build that is to keep nothing ourselves while waiting: Telegram already holds the file, so we remember only a short reference to it, with a time limit. No answer means nothing was stored.

## Read first

- `api/app/telegram/callbacks.py`: button arguments are at most 22 characters, far shorter than a Telegram `file_id`, hence the short reference.
- `api/app/telegram/sessions.py` and `api/app/redis.py`.

## Design

- **Pattern:** Port + placeholder adapter for "keep" (storage does not exist yet), idempotent handlers behind signed buttons.
- **Data flow:** feature finishes → `ask_keep_media(...)` → Redis `tg:media:<ref>` (TTL 24 h) + message with Keep / Discard → tap → handler → `keep_media` port or delete the reference.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/media.py` (changed).
- `api/app/telegram/handlers.py`, `templates.py` (changed).
- `api/tests/test_telegram_keep_media.py` (new).

**Reference store** (Redis, via two small functions taking the client)

- `async def remember_media(redis, file_id: str, mime_type: str, source: str) -> str`: stores JSON under `tg:media:<ref>` with `EX 86400`; `ref` is 16 characters from `secrets.token_urlsafe`. `source` is the feature that processed it (`braindump`, `expenses`, `vault`).
- `async def recall_media(redis, ref) -> PendingMedia | None`, `async def forget_media(redis, ref) -> None`.

**Asking**

```python
def keep_media_reply(ref: str) -> Reply
```
Template `keep_media` = `Keep this file?` with one row of buttons: `Keep` → action `media.keep`, `Discard` → action `media.discard`, both with `arg=ref`.

**Handlers** (both idempotent: a second tap finds no reference and replies `media_already_handled`)

- `media.discard`: `forget_media`; reply `media_discarded` = `Discarded. Nothing was stored.`
- `media.keep`: calls the port `KeepMedia = Callable[[PendingMedia], Awaitable[None]]`. Until file storage exists (F-3 Drive, F-4 hashing), the registered adapter is `keep_not_available`: it replies `media_keep_unavailable` = `Saving files isn't set up yet. I'll hold the reference for 24 hours.` and leaves the reference in place.
- No tap within 24 hours: Redis drops the reference. Equivalent to Discard.

**Rule for feature authors**, in the module docstring: after processing any media, call `ask` with `keep_media_reply`; never persist file bytes before a Keep.

## Steps

1. Reference store with TTL tests.
2. `keep_media_reply`.
3. The two handlers and the port with its placeholder.
4. Templates and registry entries.

## Tests

- `test_remember_sets_24h_ttl`
- `test_discard_forgets_reference_and_confirms`
- `test_keep_calls_port_with_pending_media`
- `test_keep_placeholder_leaves_reference`
- `test_second_tap_replies_already_handled`
- `test_expired_reference_behaves_like_already_handled`
- `test_ref_fits_callback_arg_limit`

## Acceptance criteria

- [ ] No file bytes are stored anywhere by this ticket
- [ ] A file is passed to the keep port only after a verified Keep tap
- [ ] References expire after 24 hours without any job
- [ ] Both handlers are safe to trigger twice
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

With the dev bot, once a feature processes media: both buttons appear; Discard confirms; tapping again says it was already handled.

## Review guide

Read the diff in this order, and check:

1. What is stored in Redis: a file ID and a mime type, no content.
2. The keep path: nothing is saved without the tap.
3. Idempotency of both handlers.

Things that should *not* be in the diff: actual storage to Drive; the feature flows that call it.

## Out of scope

- Real storage behind `KeepMedia` → F-3 / F-4.
- Calling `keep_media_reply` after parsing → EPIC-002, 003, 006.

## Assumptions

- "Always ask" is taken literally: every file, every time, with no per-type default.
- An unanswered prompt discards after 24 hours. Say so if you would rather it wait indefinitely or remind you.

## Notes / log

The agent adds progress notes, decisions and open questions here.
