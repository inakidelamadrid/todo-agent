# BE-090: DumpParser port, strict result schema and fake

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-089
- **Can run in parallel with:** BE-092
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~10 min

## Goal

The inbox has one agreed shape for "split this dump into items" (`DumpParser`), a strict schema for what a parser returns, a fake for tests, and an `unconfigured_parser` so the app runs without n8n.

## Why this ticket exists

The outline decided the inbox owns its parser port instead of extending EPIC-008's `N8nClient`. That keeps M4–M7 independent of BE-037/038: the routes call `parser(raw_text, today)` and never learn whether n8n, Claude or a fake is behind it. The n8n adapter is BE-091.

## Read first

- `api/app/telegram/sender.py` (BE-018): the port style (frozen dataclass of callables / a function type, plain error type).
- `api/tests/fakes.py`: where fakes live.
- `tickets/backend/BE-036-n8n-response-schemas.md`: how strict n8n output schemas are written (same rules here).

## Design

- **Pattern:** Ports and adapters. The port is a function type; adapters are functions; the fake ships first.
- **Data flow:** route → `parser(raw_text, today)` → `ParseDumpResult` | raises `ParserError`.

## Packages

None new.

## Details

**Files:** `api/app/inbox/parser.py` (new), `api/tests/fakes.py` (changed: `fake_parser`), `api/tests/test_dump_parser_port.py` (new).

```python
class ParsedItem(BaseModel):          # frozen, extra="forbid", camelCase
    payload: ItemPayload
    confidence: Annotated[float, Field(ge=0, le=1)]
    source_span: Annotated[str, Field(max_length=4000)]

class ParseDumpResult(BaseModel):     # frozen, extra="forbid"
    items: Annotated[tuple[ParsedItem, ...], Field(max_length=20)]

class ParserError(Exception): ...     # message names the failure kind only, never dump text

DumpParser = Callable[[str, date], Awaitable[ParseDumpResult]]   # raw text, today in America/Mexico_City

def unconfigured_parser() -> DumpParser   # always raises ParserError("dump parser is not configured")
def get_dump_parser(request: Request) -> DumpParser   # FastAPI dependency: request.app.state.dump_parser
```

`api/app/main.py` lifespan sets `app.state.dump_parser = unconfigured_parser()` (BE-091 swaps in n8n when configured). Tests override `get_dump_parser`.

Fake: `fake_parser(items=(...), fail=False, calls: list | None = None) -> DumpParser`, recording `(raw_text, today)` calls.

Example parser JSON (also the n8n contract, exported in BE-091):

```json
{"items":[
  {"payload":{"type":"task","title":"Call dentist","size":"S","dueDate":"2026-11-28","firstStep":"Find the number"},"confidence":0.92,"sourceSpan":"call dentist next week"},
  {"payload":{"type":"expense","description":"Gym","amountCents":60000,"currency":"MXN"},"confidence":0.81,"sourceSpan":"pay gym 600"}]}
```

## Steps

1. Result models and error.
2. Port type, `unconfigured_parser`, dependency, lifespan line.
3. Fake and tests.

## Tests

- `test_result_rejects_more_than_20_items`
- `test_result_rejects_unknown_fields`
- `test_unconfigured_parser_raises_parser_error`
- `test_fake_parser_records_calls_and_returns_items`
- `test_parser_error_message_has_no_dump_text`

## Acceptance criteria

- [ ] No route or feature code imports anything n8n-specific
- [ ] The app starts with no parser configured
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "
import asyncio, datetime; from tests.fakes import fake_parser
from app.inbox.parser import unconfigured_parser
print(asyncio.run(fake_parser()('buy cat food', datetime.date.today())))
asyncio.run(unconfigured_parser()('x', datetime.date.today()))"
```

Prints the fake's result, then raises `ParserError: dump parser is not configured`.

## Review guide

1. Port: a plain function type; no class hierarchy.
2. Schema: strict (forbid, bounds, max 20 items).

Things that should *not* be in the diff: httpx, n8n URLs (BE-091).

## Out of scope

- The n8n adapter → BE-091.

## Notes / log
