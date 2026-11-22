# BE-106: POST /now/{suggestionId}/action

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 10, §8 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-088, BE-105
- **Can run in parallel with:** M10 frontend presentational tickets
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~10 min

## Goal

The UI records what you did with a suggestion: **Start**, **Another** or **Not today**. Not today snoozes the task until tomorrow, without penalty.

## Why this ticket exists

Closes M9. Rerolls feed the skip penalty; Not today needs the BE-088 snooze transition.

## Read first

- `api/app/now/repository.py` (BE-104), `api/app/tasks/domain.py` and the `apply_status` repository function (BE-088).

## Design

- **Pattern:** Thin controller; status change via `transition` + `apply_status`.

## Packages

None new.

## Details

**Files:** `api/app/now/schemas.py` (changed: `SuggestionAction`, `ActionIn`), `api/app/now/router.py` (changed), `api/tests/test_now_actions_api.py` (new).

| Request | Response |
|---|---|
| `POST /now/{id}/action {"action":"started"}` | `200 {"suggestionId","action","task"}` |
| `{"action":"rerolled"}` | `200` (task unchanged) |
| `{"action":"not-today"}` | `200`; task `snoozed` until tomorrow (Mexico City date) |
| action already recorded | `409 {"detail":"This suggestion already has an answer"}` |
| unknown id | `404` |
| no / wrong credentials | `401` |

"Without penalty": not-today doesn't touch the task's score beyond being snoozed (the skip penalty only matters if it comes back today, which it can't).

## Steps

1. Schemas.
2. Route + tests.

## Tests

- `test_started_records_action`
- `test_rerolled_makes_task_a_recent_skip`
- `test_not_today_snoozes_until_tomorrow`
- `test_second_action_409`
- `test_actions_require_credentials`

## Acceptance criteria

- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

M9 demo in `/docs`: `POST /now` → take `suggestionId` → `rerolled` → `POST /now` again gives a different task; `not-today` on that one → `GET /tasks/{id}` shows `snoozed` with tomorrow's date.

## Review guide

1. Not-today uses `transition`; no status `if`.

## Out of scope

- Focus sessions → BE-107/108.

## Notes / log
