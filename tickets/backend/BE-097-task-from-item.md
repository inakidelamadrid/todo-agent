# BE-097: Turn an inbox item into a task (pure)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5, §5.3 · Milestone M6 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-081, BE-089
- **Can run in parallel with:** M4, M5 tickets
- **Public endpoint?** no
- **Review size:** ~70 lines, 3 files, ~8 min

## Goal

`task_from_item(payload, edits, item_id)` returns the `TaskCreate` that accepting this item should create, or a reason it can't be accepted.

## Why this ticket exists

Accept (BE-098) and Accept all (BE-100) both convert items to tasks. One pure function means they can't disagree, and the conversion rules (reminder → dated task; notes and expenses wait) are reviewed alone.

## Read first

- `api/app/inbox/schemas.py` (BE-089), `api/app/tasks/schemas.py` (BE-080).

## Design

- **Pattern:** Plain function + Result over exceptions.

## Packages

None new.

## Details

**Files:** `api/app/inbox/accept.py` (new), `api/app/inbox/schemas.py` (changed: `TaskEdits`), `api/tests/test_task_from_item.py` (new).

```python
class TaskEdits(_CamelModel):   # every TaskCreate field except parentId/createdFrom, all optional, extra="forbid"
    ...

class NotAcceptable(StrEnum):
    NOTE = "notes-arrive-later"
    EXPENSE = "expenses-go-to-epic-002"

def task_from_item(payload: ItemPayload, edits: TaskEdits | None, item_id: UUID) -> TaskCreate | NotAcceptable
```

| Payload | Result |
|---|---|
| `task` | `TaskCreate` from its fields (defaults for missing size/energy/context), edits applied on top, `created_from = item_id` |
| `reminder` | `TaskCreate(title, due_date=d, do_date=d, size=XS)`, edits on top |
| `note` | `NotAcceptable.NOTE` |
| `expense` | `NotAcceptable.EXPENSE` |

Edits are merged with `model_copy(update=edits.model_dump(exclude_unset=True))` then re-validated through `TaskCreate`, so an edit can't bypass limits.

## Steps

1. `TaskEdits`.
2. Function with a `match` on `payload.type`.
3. Tests.

## Tests

- `test_task_payload_becomes_task_with_defaults`
- `test_reminder_becomes_dated_xs_task`
- `test_edits_override_parsed_fields`
- `test_edits_are_revalidated` (title too long → error)
- `test_note_and_expense_not_acceptable`

## Acceptance criteria

- [ ] Pure; no session, no I/O
- [ ] `match` covers every payload type (a new type fails type-checking)
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "
import uuid; from app.inbox.accept import task_from_item; from app.inbox.schemas import ReminderPayload
print(task_from_item(ReminderPayload(type='reminder', title='Permission slip', due_date='2026-11-20'), None, uuid.uuid4()))"
```

Prints a `TaskCreate` with `size='XS'` and both dates set.

## Review guide

1. Reminder rule matches the outline's assumption.
2. Edits re-validated.

## Out of scope

- Notes entity and EPIC-002 routing → deferred.

## Notes / log
