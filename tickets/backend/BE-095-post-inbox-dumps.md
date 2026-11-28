# BE-095: POST /inbox/dumps

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2, §8 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-093, BE-094
- **Can run in parallel with:** BE-096
- **Public endpoint?** no
- **Review size:** ~110 lines, 3 files, ~12 min

## Goal

`POST /inbox/dumps` stores a dump, asks the parser to split it, stores the resulting items, and returns them. If the parser fails or isn't configured, the raw text is still saved as one fallback item.

## Why this ticket exists

This is capture: the first half of the epic's loop. The fallback means capture works today, with no n8n, and still works when n8n is down later.

## Read first

- `api/app/inbox/parser.py` (BE-090), `api/app/inbox/mapping.py` and `api/app/clock.py` (BE-093).
- `api/app/telegram/webhook.py`: how a fixed pipeline of small steps is laid out in a route.

## Design

- **Pattern:** Pipeline: `today_in` → `parser` → `drafts_from_result` (or `fallback_draft` on `ParserError`) → `save_dump` → response.

## Packages

None new.

## Details

**Files:** `api/app/inbox/router.py` (new), `api/app/main.py` (changed: mount `inbox_router` with `require_principal`), `api/tests/test_inbox_dumps_api.py` (new).

Request: `{"rawText":"call dentist next week, also buy cat food","source":"web"}`

Response `201`:

```json
{"dump":{"id":"…","rawText":"call dentist next week, also buy cat food","source":"web","receivedAt":"…"},
 "items":[{"id":"…","dumpId":"…","payload":{"type":"task","title":"call dentist next week, also buy cat food","firstStep":""},
           "confidence":0.0,"sourceSpan":"call dentist next week, also buy cat food","status":"new","snoozedUntil":null,
           "createdAt":"…","rawText":"…"}],
 "parsed":false}
```

`parsed` is `true` when the parser answered, `false` when the fallback was used, so the UI can say "Saved as is".

| Case | Response |
|---|---|
| valid | `201` as above |
| empty / too long `rawText` | `422` |
| parser raises `ParserError` | `201` with the fallback item, `parsed: false`; log `inbox.parse_failed` with the error kind only, never the text |
| no / wrong credentials | `401` |

Privacy: the dump text is sent only to the parser (epic §9), and never logged.

## Steps

1. Router with the pipeline; dependencies `get_session`, `get_dump_parser`, `utc_now`.
2. Mount.
3. Tests with `fake_parser`.

## Tests

- `test_dump_with_fake_parser_saves_items` (`parsed: true`)
- `test_parser_gets_today_in_mexico_city` (override `utc_now`)
- `test_parser_failure_saves_fallback_item` (`parsed: false`)
- `test_unconfigured_parser_saves_fallback_item`
- `test_dump_text_not_in_logs` (caplog)
- `test_dumps_require_credentials` (missing and wrong key → `401`)

## Acceptance criteria

- [ ] A dump is never lost: every successful request stores the dump and at least one item
- [ ] Endpoint rejects requests without valid credentials
- [ ] Dump text never appears in logs
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
curl -s -X POST http://127.0.0.1:8000/inbox/dumps -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"rawText":"call dentist, buy cat food","source":"web"}' | python3 -m json.tool
```

`201`, one item, `"parsed": false` (no n8n yet).

## Review guide

1. The pipeline reads top to bottom, one step per line.
2. `except ParserError` is the only exception caught.
3. Logging: kind only.

Things that should *not* be in the diff: `GET /inbox` (BE-096), the n8n adapter.

## Out of scope

- Telegram messages becoming dumps → deferred (Telegram capture).

## Notes / log
