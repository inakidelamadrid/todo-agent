# BE-093: Map parser output to inbox drafts, and today in Mexico City

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-090
- **Can run in parallel with:** BE-092, BE-094
- **Public endpoint?** no
- **Review size:** ~90 lines, 4 files, ~10 min

## Goal

Two pure modules: `inbox/mapping.py` turns a parser result into item drafts (or one fallback draft), and `clock.py` answers "what date is it in Mexico City right now?".

## Why this ticket exists

A parser is an LLM in the end, so its output is shaped but not trusted: dates can be absurd, spans can be invented, and it can return nothing. One mapping function at the edge cleans that up, and a fallback guarantees a dump never vanishes. Relative dates must resolve in America/Mexico_City (epic §5.2), so the API needs one place that computes "today" there; snooze (BE-099) and What now? (BE-105) reuse it.

## Read first

- **Anti-corruption layer:** one function at the boundary converts foreign output into our types, so nothing deeper sees the foreign shape.
- `zoneinfo` docs: <https://docs.python.org/3/library/zoneinfo.html>.

## Design

- **Pattern:** Anti-corruption layer (mapping) + functional core (both modules pure; `utc_now` is the only side effect, injected as a FastAPI dependency).

## Packages

None new (`zoneinfo` is standard library; Docker images running the API must include `tzdata`, noted in the outline).

## Details

**Files:** `api/app/clock.py` (new), `api/app/inbox/mapping.py` (new), `api/tests/test_clock.py`, `api/tests/test_inbox_mapping.py` (new).

```python
# clock.py
APP_TZ = ZoneInfo("America/Mexico_City")
def utc_now() -> datetime                          # side effect; a FastAPI dependency tests override
def today_in(tz: ZoneInfo, now: datetime) -> date  # pure; now must be timezone-aware

# inbox/mapping.py
@dataclass(frozen=True)
class ItemDraft:
    payload: ItemPayload
    confidence: float
    source_span: str

def drafts_from_result(result: ParseDumpResult, raw_text: str, today: date) -> tuple[ItemDraft, ...]
def fallback_draft(raw_text: str) -> ItemDraft
```

`drafts_from_result` rules:

- A `source_span` that isn't a substring of `raw_text` (case-insensitive) becomes `""` and the confidence is capped at 0.5.
- Dates earlier than `today - 365 days` or later than `today + 5 years` are set to `None` (reminders with a bad date become tasks without a date, confidence capped at 0.5).
- No items → `(fallback_draft(raw_text),)`.

`fallback_draft`: a `task` payload whose title is the first line of the dump cut to 120 characters (ellipsis if cut), `confidence = 0.0` (so Accept all never takes it), `source_span = raw_text[:4000]`.

## Steps

1. `clock.py` + tests.
2. `mapping.py` + tests.

## Tests

- `test_today_in_mexico_city_before_midnight_utc` (2026-11-23T03:00Z → 2026-11-22)
- `test_today_in_rejects_naive_datetime`
- `test_invented_span_is_cleared_and_confidence_capped`
- `test_absurd_dates_dropped`
- `test_empty_result_gives_fallback`
- `test_fallback_title_is_first_line_trimmed_to_120`

## Acceptance criteria

- [ ] Both modules have no I/O except `utc_now`
- [ ] A dump can never map to zero drafts
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "
from datetime import datetime, timezone; from app.clock import APP_TZ, today_in
print(today_in(APP_TZ, datetime(2026,11,23,3,0,tzinfo=timezone.utc)))"
```

Prints `2026-11-22`.

## Review guide

1. `today_in`: refuses naive datetimes.
2. Mapping: every rule above has a test; nothing raises on bad parser output.

Things that should *not* be in the diff: DB writes, routes.

## Out of scope

- Saving drafts → BE-094/095.

## Notes / log
