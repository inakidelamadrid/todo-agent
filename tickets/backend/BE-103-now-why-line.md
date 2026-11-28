# BE-103: The "why" line for a suggestion

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 10, §5.5, §6 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-102
- **Can run in parallel with:** BE-104
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files, ~6 min

## Goal

`why_line(scored, req, today)` turns the strongest factors into one short, kind sentence, e.g. "Due tomorrow, fits your 15 min, low energy is OK."

## Why this ticket exists

The *why* is what makes the suggestion trustworthy. The outline decided on a fixed template now and AI wording later; a pure template is fast (the epic's < 1 s target) and testable.

## Read first

- `api/app/now/scoring.py` (BE-102).
- Epic §6 Language: kind and neutral, "past its date", never "overdue!!!".

## Design

- **Pattern:** Plain function: ordered phrase rules, first three that apply.

## Packages

None new.

## Details

**Files:** `api/app/now/why.py` (new), `api/tests/test_now_why.py` (new).

Phrase rules, in order (take at most three, join with ", ", capitalise first, end with "."):

| When | Phrase |
|---|---|
| due date past | "Past its date, a small step helps" |
| due today | "Due today" |
| due tomorrow | "Due tomorrow" |
| due in 2–7 days | "Due Friday" (weekday name) |
| `req.available_minutes` set and fits | "fits your 15 min" (`60` → "fits your hour") |
| task energy low and req energy low | "low energy is OK" |
| momentum | "keeps a started task moving" |
| age ≥ 0.5 | "it's been waiting a while" |
| nothing above | "A good next step" |

No exclamation marks, no "overdue", "late" or "should".

## Steps

1. Function + tests.

## Tests

- `test_due_tomorrow_and_fits_time`
- `test_past_date_wording_is_calm`
- `test_at_most_three_phrases`
- `test_fallback_phrase`
- `test_no_forbidden_words` (scan every rule's output)

## Acceptance criteria

- [ ] Pure; English only in Phase 1 (bot replies in Spanish/English come with Telegram `/now`)
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Extend BE-102's `--demo` to print the why line under each sample, and read them out loud: do they sound kind?

## Review guide

1. Wording table vs code; forbidden-words test.

## Out of scope

- AI-written *why* → deferred.

## Notes / log
