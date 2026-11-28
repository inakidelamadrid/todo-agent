# BE-091: n8n adapter for DumpParser

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M8 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-038, BE-041, BE-090, BE-110, BE-113
- **Can run in parallel with:** M9–M11 tickets
- **Public endpoint?** no
- **Review size:** ~80 lines, 5 files, ~10 min

## Goal

With `DUMP_PARSER=n8n`, the API sends each dump to n8n's `parse_dump` webhook with an HMAC-signed request and validates the answer against `ParseDumpResult`.

## Why this ticket exists

The real parser. It reuses EPIC-008's signed httpx client (BE-038) and schema export (BE-041) instead of new plumbing, and plugs into the port from BE-090, so no inbox code changes.

## Read first

- `api/app/n8n/http_client.py` (BE-038): `sign_request`, the error rules, the lifespan client.
- `api/scripts/export_n8n_schemas.py` and `integrations/n8n/README.md` (BE-041).
- `api/app/inbox/parser.py` (BE-090).

## Design

- **Pattern:** Adapter (implements the `DumpParser` port) + anti-corruption (n8n's JSON is parsed into `ParseDumpResult` at the edge).

## Packages

None new (`httpx` promoted to runtime by BE-038).

## Details

**Files:** `api/app/inbox/n8n_parser.py` (new), `api/app/main.py` (changed: `dump_parser == "n8n"` + n8n configured → this adapter, else startup error naming the missing settings), `api/scripts/export_n8n_schemas.py` (changed: also writes `parse_dump.request.schema.json` and `parse_dump.response.schema.json`), `integrations/n8n/schemas/` (regenerated), `api/tests/test_n8n_dump_parser.py` (new).

```python
def n8n_dump_parser(http: httpx.AsyncClient, base_url: str, secret: str, clock=time.time) -> DumpParser
```

- `POST {base_url}/webhook/parse-dump`, body `{"rawText": "...", "today": "2026-11-22", "timezone": "America/Mexico_City", "languages": ["es","en"]}`, headers `X-Timestamp`, `X-Signature: sha256=<hex>` from `sign_request`.
- Timeout 20 s (the epic's ≤10 s target is end to end; the fallback covers slow runs).
- Timeout, connection error, non-2xx, non-JSON or schema failure → `ParserError(kind)`; BE-095 then saves the fallback.

## Steps

1. Adapter + `MockTransport` tests.
2. Lifespan selection.
3. Schema export and regenerate.

## Tests

- `test_sends_signed_request_with_today_and_timezone`
- `test_valid_response_returns_result`
- `test_extra_field_in_response_raises_parser_error`
- `test_timeout_raises_parser_error`
- `test_committed_parse_dump_schemas_match_models` (BE-041's staleness test covers the new files)

## Acceptance criteria

- [ ] `make n8n-schemas` produces no diff after the change
- [ ] Any n8n failure becomes `ParserError`, never a 500
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make n8n-schemas && git status --short integrations/   # clean
cd api && uv run pytest -k n8n_dump_parser -v
```

The end-to-end check against a real workflow is BE-112.

## Review guide

1. Signature bytes identical to BE-038's `sign_request`.
2. Errors carry the kind only.

Things that should *not* be in the diff: workflow JSON (BE-112).

## Out of scope

- The n8n workflow → BE-112.

## Notes / log
