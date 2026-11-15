# BE-037: n8n client port and fake

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.4, §2
- **Assigned agent / harness / model:**
- **Depends on:** BE-036
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files, ~8 min

## Goal

The app has one agreed shape for "transcribe this audio" and "read this image", plus a fake for tests.

## Why this ticket exists

The epic's goal is that AI parsing can move between n8n and the API without changing feature code. That is what a port gives: features call `ai.transcribe(...)` and never learn that n8n is behind it.

## Read first

- `api/app/telegram/sender.py` (BE-018): the same port style.

## Design

- **Pattern:** Port + fake.
- **Data flow:** feature → `N8nClient.transcribe(bytes, mime)` → `TranscribeResult`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/n8n/client.py` (new).
- `api/tests/fakes.py` (changed): `fake_n8n(transcribe_text="…", ocr_text="…", fail=False)`.
- `api/tests/test_n8n_port.py` (new).

**Types**

```python
class N8nError(Exception): ...                    # any failure: network, status, bad JSON, schema

@dataclass(frozen=True)
class N8nClient:
    transcribe: Callable[[bytes, str], Awaitable[TranscribeResult]]   # content, mime type
    ocr: Callable[[bytes, str], Awaitable[OcrResult]]
```

`unconfigured_n8n() -> N8nClient`: both operations raise `N8nError("n8n is not configured")`, so the app starts without n8n.

## Steps

1. Define the port and the error.
2. Write the fake and `unconfigured_n8n`.
3. Tests.

## Tests

- `test_fake_returns_configured_results`
- `test_fake_can_fail_with_n8n_error`
- `test_unconfigured_client_raises_n8n_error`

## Acceptance criteria

- [ ] `client.py` has no HTTP imports
- [ ] Callers only ever need to catch `N8nError`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The two operations and the single error type.

Things that should *not* be in the diff: httpx, HMAC, settings.

## Out of scope

- The real client → BE-038.

## Notes / log

The agent adds progress notes, decisions and open questions here.
