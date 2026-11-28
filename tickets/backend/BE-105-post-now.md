# BE-105: POST /now

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 stories 9–10, §5.5, §8 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-085, BE-093, BE-103, BE-104
- **Can run in parallel with:** M10 frontend presentational tickets
- **Public endpoint?** no
- **Review size:** ~110 lines, 4 files, ~12 min

## Goal

`POST /now` returns one task to do now, a readable *why*, and up to two alternates, and records the suggestion.

## Why this ticket exists

Joins the pure engine (BE-101–103) to the data. The pipeline stays visible in the route so you can read the whole decision in one screen.

## Read first

- `api/app/now/domain.py`, `scoring.py`, `why.py`, `repository.py`; `api/app/clock.py`.

## Design

- **Pattern:** Pipeline: load → snapshot → filter → score → rank → pick → why → record → respond.

## Packages

None new.

## Details

**Files:** `api/app/tasks/repository.py` (changed: `open_child_parent_ids(session)`, `started_parent_ids(session)`), `api/app/now/router.py` (new), `api/app/main.py` (changed: mount with `require_principal`), `api/tests/test_now_api.py` (new).

Request: `{"energy":"low","availableMinutes":15,"context":null}` (all optional).

Response `200`:

```json
{"suggestionId":"…","task":{…TaskOut…},"why":"Due tomorrow, fits your 15 min, low energy is OK.",
 "alternates":[{"task":{…},"why":"…"},{"task":{…},"why":"…"}]}
```

No candidates → `200 {"suggestionId":null,"task":null,"why":null,"alternates":[]}` (the UI shows the kind reset, epic story 12).

- `today = today_in(APP_TZ, utc_now())`; `recent_skips = recent_skipped_task_ids(now - 6h)`.
- Only the main pick is recorded; alternates get a suggestion row when the UI shows them (the UI calls `POST /now` again after a reroll, excluding nothing extra because the reroll is now a recent skip).
- `422` on invalid values; `401` without credentials.
- Target: < 1 s with 500 tasks (one query for tasks, two small queries for parent sets).

## Steps

1. Repository helpers.
2. Route with the pipeline.
3. Mount; tests.

## Tests

- `test_now_returns_due_tomorrow_task_with_why`
- `test_now_respects_available_minutes`
- `test_now_no_candidates_returns_nulls`
- `test_now_records_suggestion_with_factors`
- `test_now_skipped_task_ranks_lower_after_reroll`
- `test_now_requires_credentials` (missing and wrong key → `401`)

## Acceptance criteria

- [ ] Pipeline reads top to bottom in the route
- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Create three tasks in `/docs` (due tomorrow S low; M high no date; L), then `POST /now {"energy":"low","availableMinutes":15}` → the due-tomorrow one with a sensible why; the L task never appears.

## Review guide

1. The pipeline order.
2. No logic duplicated from the pure modules.

## Out of scope

- Recording actions → BE-106.

## Notes / log
