# BE-096: GET /inbox

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3, §8 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-094
- **Can run in parallel with:** BE-095
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files, ~6 min

## Goal

`GET /inbox` returns the untriaged items, newest first, each with its original dump text.

## Why this ticket exists

Closes M4: you can see what capture stored. The web Inbox (M5) reads this.

## Read first

- `api/app/inbox/router.py` (BE-095), `api/app/inbox/repository.py` (BE-094).

## Design

- **Pattern:** Thin controller.

## Packages

None new.

## Details

**Files:** `api/app/inbox/router.py` (changed), `api/tests/test_inbox_list_api.py` (new).

| Request | Response |
|---|---|
| `GET /inbox` | `200 InboxItemOut[]` (new items + snoozed items whose time has come) |
| no / wrong credentials | `401` |

`now` comes from the `utc_now` dependency so tests can move time.

## Steps

1. Route.
2. Tests.

## Tests

- `test_inbox_empty`
- `test_inbox_lists_new_items_newest_first`
- `test_inbox_items_include_raw_text`
- `test_inbox_requires_credentials`

## Acceptance criteria

- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

M4 demo: after the `curl` in BE-095, `GET /inbox` in `/docs` shows the item with your raw text.

## Review guide

1. Route has no logic beyond calling `list_inbox`.

## Out of scope

- Triage actions → M6/M7.

## Notes / log
