# BE-038: n8n httpx client with HMAC-signed requests

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.4, §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-037
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~100 lines, 4 files, ~15 min

## Goal

The real n8n client posts to n8n's webhooks with a signature n8n can verify, and returns validated results or `N8nError`.

## Why this ticket exists

The API sends your voice notes and photos to n8n. The signature proves to n8n that the request is from the API and was not altered, and the timestamp stops a captured request from being replayed later.

## Read first

- https://www.python-httpx.org/async/ and `httpx.MockTransport` (testing without a network).
- `api/app/telegram/callbacks.py` (BE-022): HMAC is already used there.
- This is the outbound direction (API → n8n). n8n must verify the signature in its workflow; that side is documented in BE-041.

## Design

- **Pattern:** Adapter behind the `N8nClient` port; signing is a pure function.
- **Data flow:** `bytes` → JSON body → `sign_request(body, timestamp, secret)` → `POST {base}/webhook/<operation>` → parse with BE-036 schemas.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `httpx` | installed as a dev dependency; **promote to runtime** | Async HTTP client | 0.28.1, BSD-3-Clause. Already in the project for tests and is what FastAPI's test client uses. Note: its last release was 2024-12-06, older than our one-year guideline; kept because it is already a dependency and has no maintained drop-in successor in our stack. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): move `httpx` to runtime dependencies (`uv add httpx`).
- `api/app/settings.py` (changed): `n8n_base_url: str = ""` (must be `https://…`, or `http://127.0.0.1`/`http://localhost` for dev), `n8n_shared_secret: SecretStr = SecretStr("")` (minimum 32 characters when set). Add both to `api/.env.example`.
- `api/app/n8n/http_client.py` (new).
- `api/tests/test_n8n_http_client.py` (new).

**Request**

- `POST {n8n_base_url}/webhook/transcribe` and `/webhook/ocr`.
- Body (JSON): `{"mimeType": "audio/ogg", "contentBase64": "…"}`.
- Headers: `X-Timestamp: <unix seconds>`, `X-Signature: sha256=<hex>`.
- Timeout 30 s. No automatic retries here.

**Functions**

- `sign_request(body: bytes, timestamp: int, secret: str) -> str` (pure): hex HMAC-SHA256 over `f"{timestamp}.".encode() + body`.
- `httpx_n8n_client(http: httpx.AsyncClient, base_url: str, secret: str, clock: Callable[[], float] = time.time) -> N8nClient`.
- Any of these becomes `N8nError`: timeout or connection error; non-2xx status; body not JSON; schema validation failure. The error message names the operation and the kind of failure only, never the content.
- The `httpx.AsyncClient` is created in the lifespan when both settings are set; otherwise `unconfigured_n8n()`.

## Steps

1. Promote `httpx`.
2. Settings.
3. `sign_request` with a known-answer test.
4. The client with `MockTransport` tests.
5. Lifespan wiring.

## Tests

- `test_sign_request_known_answer`: fixed body, timestamp and secret → fixed hex.
- `test_request_carries_timestamp_and_matching_signature`
- `test_valid_response_parses`
- `test_non_2xx_raises_n8n_error`
- `test_timeout_raises_n8n_error`
- `test_extra_field_in_response_raises_n8n_error`
- `test_error_message_has_no_content`
- `test_plain_http_base_url_is_rejected_unless_local`

## Acceptance criteria

- [ ] Every request is signed over timestamp and body
- [ ] A non-HTTPS base URL is refused except for localhost
- [ ] All failures surface as `N8nError`
- [ ] The secret and the file content never appear in logs or errors
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

End to end requires the n8n workflows from BE-041.

## Review guide

Read the diff in this order, and check:

1. `sign_request`: what exactly is signed.
2. The four failure paths, each ending in `N8nError`.
3. `settings.py`: the URL rule.

Things that should *not* be in the diff: retries; calling the client from a handler (the feature epics do that, inside a job).

## Out of scope

- The n8n side of the contract → BE-041.
- Using it for voice notes → EPIC-003.

## Notes / log

The agent adds progress notes, decisions and open questions here.
