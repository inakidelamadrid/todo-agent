# BE-089: Inbox schemas: dumps and candidate items

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2, §5.3, §7 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-080
- **Can run in parallel with:** BE-081–088
- **Public endpoint?** no (no routes)
- **Review size:** ~120 lines, 2 files, ~12 min

## Goal

`api/app/inbox/schemas.py` defines what a dump is, the four kinds of candidate item as a discriminated union, and what the inbox returns.

## Why this ticket exists

A dump becomes several candidate items of different shapes (task, note, expense, reminder). Fixing those shapes first lets the parser port (BE-090), the table (BE-092) and the routes be built against one contract.

## Read first

- `api/app/bills/schemas.py`: `_CamelModel`, `MAX_CENTS`, `Currency`.
- `api/app/tasks/schemas.py` (BE-080): `TaskSize`, `Energy`, `TaskContext`, title limits (reuse them).
- **Discriminated union:** a union whose members share a `type` field with a different literal value each; Pydantic reads `type` and validates against the matching model only. <https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions>

## Design

- **Pattern:** Discriminated union + parse, don't validate. Every payload model uses `extra="forbid"`.

## Packages

None new.

## Details

**Files:** `api/app/inbox/__init__.py`, `api/app/inbox/schemas.py` (new), `api/tests/test_inbox_schemas.py` (new).

```python
class DumpSource(StrEnum): TELEGRAM_TEXT="telegram-text"; TELEGRAM_VOICE="telegram-voice"; TELEGRAM_PHOTO="telegram-photo"; WEB="web"
class InboxItemType(StrEnum): TASK="task"; NOTE="note"; EXPENSE="expense"; REMINDER="reminder"
class InboxItemStatus(StrEnum): NEW="new"; ACCEPTED="accepted"; DISCARDED="discarded"; SNOOZED="snoozed"
```

| Model | Fields |
|---|---|
| `DumpIn` | `rawText` str trimmed 1–4000; `source` `DumpSource` (default `web`) |
| `TaskPayload` | `type: Literal["task"]`; `title` 1–120; `size` / `energy` / `context` optional; `doDate`, `dueDate` optional dates; `firstStep` 0–200 default `""` |
| `ReminderPayload` | `type: Literal["reminder"]`; `title` 1–120; `dueDate` date (required) |
| `NotePayload` | `type: Literal["note"]`; `title` 1–120; `body` 0–2000 default `""` |
| `ExpensePayload` | `type: Literal["expense"]`; `description` 1–120; `amountCents` int 0–`MAX_CENTS`; `currency` `Currency` default `MXN`; `spentOn` date optional |
| `ItemPayload` | `Annotated[TaskPayload \| ReminderPayload \| NotePayload \| ExpensePayload, Field(discriminator="type")]` |
| `DumpOut` | `id`, `rawText`, `source`, `receivedAt` |
| `InboxItemOut` | `id`, `dumpId`, `payload: ItemPayload`, `confidence` float 0–1, `sourceSpan` str 0–4000, `status`, `snoozedUntil` datetime \| null, `createdAt`, `rawText` (the whole dump, so "what I originally said" is always visible) |

Money stays integer cents. Confidence is a probability, not money, so a float is fine.

## Steps

1. Enums, `DumpIn`.
2. Payload models and the union.
3. Out models.
4. Tests.

## Tests

- `test_dump_text_trimmed_and_bounded` (empty → error; 4001 chars → error)
- `test_union_picks_model_by_type`
- `test_task_payload_rejects_amount_cents` (extra forbidden)
- `test_reminder_requires_due_date`
- `test_expense_amount_is_integer_cents` (`12.5` → error)
- `test_inbox_item_out_camel_case`

## Acceptance criteria

- [ ] Every payload forbids extra fields
- [ ] Task limits reuse BE-080 constants
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "
from pydantic import TypeAdapter; from app.inbox.schemas import ItemPayload as P
a=TypeAdapter(P); print(a.validate_python({'type':'reminder','title':'Permission slip','dueDate':'2026-11-20'}))
a.validate_python({'type':'task','title':'x','amountCents':600})"
```

The first prints a `ReminderPayload`; the second raises "Extra inputs are not permitted".

## Review guide

1. The union: discriminator on `type`, four members.
2. `ExpensePayload`: integer cents, currency enum reused from bills.

Things that should *not* be in the diff: parser, DB.

## Out of scope

- Parser port → BE-090. Table → BE-092.

## Notes / log
