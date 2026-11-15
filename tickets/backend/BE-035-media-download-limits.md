# BE-035: Download media with size and type limits

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Media, §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-019
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~100 lines, 4 files, ~12 min

## Goal

A voice note, photo or document can be fetched from Telegram into memory, but only when its type is allowed and its size is within the limit.

## Why this ticket exists

Files are untrusted input. The limits are checked twice: before downloading, using what Telegram says about the file, and after, using what actually arrived. The check is a pure function so the rules are easy to read and test.

## Read first

- https://core.telegram.org/bots/api#getfile: bots can download files up to 20 MB.
- Confirm every aiogram name used here against https://docs.aiogram.dev/ (v3) before coding; do not rely on memory.
- `api/app/telegram/sender.py`, `aiogram_sender.py`.

## Design

- **Pattern:** Pure validation + adapter: `check_media` decides; the sender port gains one `download` operation.
- **Data flow:** `InboundUpdate` → `check_media` → rejection, or `sender.download(file_id)` → `check_size(bytes)` → `bytes`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/media.py` (new).
- `api/app/telegram/sender.py`, `aiogram_sender.py` (changed): `download: Callable[[str], Awaitable[bytes]]` (file_id → bytes; `get_file` then `download_file` into memory).
- `api/tests/fakes.py` (changed): the fake's `download` returns configurable bytes.
- `api/tests/test_telegram_media.py` (new).

**Limits**

```python
MAX_MEDIA_BYTES = 20 * 1024 * 1024
ALLOWED_MIME_TYPES = frozenset({
    "image/jpeg", "image/png", "image/webp", "application/pdf",
    "audio/ogg", "audio/mpeg", "audio/mp4",
})
```

**Functions**

- `check_media(update: InboundUpdate) -> MediaRejection | None` (pure). `MediaRejection` is a frozen model with `reason: Literal["no_file", "type_not_allowed", "too_large"]`. A missing `file_size` is allowed here and caught after download.
- `async def fetch_media(sender, update) -> bytes | MediaRejection`: runs `check_media`, downloads, then rejects with `too_large` when `len(data) > MAX_MEDIA_BYTES`.
- Templates added: `media_type_not_allowed` = `I can only read photos, PDFs and voice notes.`; `media_too_large` = `That file is over 20 MB.`

Bytes stay in memory and are returned to the caller. Nothing is written to disk, logged or stored here; retention is decided per file by the user (BE-045).

## Steps

1. Limits and `check_media` with tests.
2. Add `download` to the port, the adapter and the fake.
3. `fetch_media`.
4. Templates.

## Tests

- `test_allowed_types_pass` (parametrised over the fixtures).
- `test_unknown_mime_type_is_rejected`
- `test_declared_size_over_limit_is_rejected_without_download`: the fake records no download call.
- `test_actual_size_over_limit_is_rejected_after_download`
- `test_update_without_file_is_rejected`
- `test_adapter_download_calls_get_file_then_download`

## Acceptance criteria

- [ ] An oversized or disallowed file is never downloaded when Telegram declares it as such
- [ ] Downloaded bytes never touch the disk
- [ ] The limits are named constants in one module
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `media.py`: the allowed list. Is anything there you would not want the app to accept?
2. `fetch_media`: both size checks.
3. No file path or temp file anywhere.

Things that should *not* be in the diff: storing files, OCR, transcription.

## Out of scope

- Asking whether to keep the file → BE-045.
- Transcription and OCR → BE-036 to BE-038.

## Notes / log

The agent adds progress notes, decisions and open questions here.
