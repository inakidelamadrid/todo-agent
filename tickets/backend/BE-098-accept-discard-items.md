# BE-098: POST /inbox/{id}/accept and /discard

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5, §8 · Milestone M6 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-084, BE-096, BE-097
- **Can run in parallel with:** FE-033–041
- **Public endpoint?** no
- **Review size:** ~110 lines, 3 files, ~12 min

## Goal

Accepting an item creates its task and marks the item accepted, in one transaction; discarding ("Let go") marks it discarded and keeps the dump.

## Why this ticket exists

The backend half of M6. The UI's Accept and Let go buttons (FE-034) call these.

## Read first

- `api/app/inbox/accept.py` (BE-097), `api/app/tasks/repository.py` (`create_task`).

## Design

- **Pattern:** Thin controller; the conversion is BE-097's pure function, the writes are repository calls in one session.

## Packages

None new.

## Details

**Files:** `api/app/inbox/repository.py` (changed: `set_item_status(session, item, status, snoozed_until=None)`), `api/app/inbox/router.py` (changed), `api/tests/test_inbox_accept_api.py` (new).

| Request | Body | Response |
|---|---|---|
| `POST /inbox/{id}/accept` | optional `TaskEdits` | `200 {"item": InboxItemOut, "task": TaskOut}` |
| accept a `note` / `expense` | — | `409 {"detail":"Notes can be accepted in a later update"}` / `"Expenses will go to the expenses flow"` |
| accept an item already accepted or discarded | — | `409` |
| `POST /inbox/{id}/discard` | — | `200 InboxItemOut` (`discarded`); discarding a discarded item is `200` (idempotent) |
| discard an accepted item | — | `409` |
| unknown id | — | `404` |
| no / wrong credentials | — | `401` |

New and snoozed items can both be accepted or discarded.

## Steps

1. `set_item_status`.
2. Accept route: load → `task_from_item` → `create_task` → `set_item_status(accepted)`.
3. Discard route.
4. Tests.

## Tests

- `test_accept_creates_task_and_marks_item`
- `test_accept_with_edits_uses_them`
- `test_accept_note_409`
- `test_accept_twice_409`
- `test_discard_is_idempotent`
- `test_discard_keeps_dump`
- `test_accept_discard_require_credentials`

## Acceptance criteria

- [ ] Task creation and item status change commit together (a failure leaves neither)
- [ ] Endpoints reject requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

In `/docs`: post a dump, accept its item → response has the task; `GET /tasks` lists it; `GET /inbox` no longer shows the item.

## Review guide

1. Both writes in one session/commit.
2. 409 messages are kind.

## Out of scope

- Snooze → BE-099; accept all → BE-100.

## Notes / log
