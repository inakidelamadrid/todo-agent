# BE-080: Task schemas

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4, §7 · Milestone M2 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-109–111, FE-035, FE-036, FE-040, FE-049
- **Public endpoint?** no (no routes)
- **Review size:** ~110 lines, 2 files, ~10 min

## Goal

`api/app/tasks/schemas.py` defines the Task enums and the frozen `TaskCreate`, `TaskUpdate` and `TaskOut` models, camelCase on the wire.

## Why this ticket exists

Tasks are the new core entity of EPIC-003: the inbox turns items into tasks, What now? picks among them, and EPIC-004/005 will read them. Every later task ticket imports these types, so the contract is fixed first, with no database and no routes.

## Read first

- `api/app/bills/schemas.py`: `_CamelModel`, `Annotated` limits, `_strip`, the `StrEnum`s. Copy this shape.
- `api/tests/test_bills_schemas.py`: how schema tests are written.

## Design

- **Pattern:** Parse, don't validate. Input is parsed once at the edge into frozen models; the core never re-checks.
- **Data flow:** JSON → `TaskCreate` / `TaskUpdate` (422 on bad input) … `Task` row → `TaskOut` → JSON.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `pydantic` | installed | models, aliases | house standard |

## Details

**Files**

- `api/app/tasks/__init__.py` (new, empty), `api/app/tasks/schemas.py` (new).
- `api/tests/test_task_schemas.py` (new).

**Enums** (`StrEnum`)

| Enum | Values |
|---|---|
| `TaskSize` | `XS` (≤5 min) · `S` (≤15) · `M` (≤45) · `L` (≤2 h) · `XL` (needs breaking down) |
| `Energy` | `low` · `medium` · `high` |
| `TaskContext` | `home` · `computer` · `phone` · `errand` · `anywhere` |
| `TaskStatus` | `active` · `snoozed` · `done` · `dropped` |

There is no `inbox` status: untriaged things are `InboxItem`s (BE-089) until accepted.

**Fields**

| Field | Type / rules | Create | Update |
|---|---|---|---|
| `title` | str, trimmed, 1–120 | required | optional |
| `notes` | str, 0–2000 | default `""` | optional |
| `size` | `TaskSize` | default `S` | optional |
| `energy` | `Energy` | default `medium` | optional |
| `context` | `TaskContext` | default `anywhere` | optional |
| `doDate` | `date` \| null | default null | optional (null clears) |
| `dueDate` | `date` \| null | default null | optional (null clears) |
| `firstStep` | str, trimmed, 0–200 | default `""` | optional |
| `parentId` | UUID \| null | default null | **not allowed** (moving tasks is out of scope) |
| `createdFrom` | UUID \| null | default null (set by the inbox, BE-098) | not allowed |

`TaskUpdate` has no `status`: status changes go through the action endpoints (BE-088). `TaskUpdate` uses `extra="forbid"` so `status` or `parentId` in a PATCH is a `422`, not silently ignored.

`TaskOut` = all of the above plus `id: UUID`, `status: TaskStatus`, `snoozedUntil: date | null`, `completedAt`, `droppedAt`, `createdAt`, `updatedAt` (`datetime | null` where not always set), `from_attributes=True`.

Example `TaskOut`:

```json
{"id":"7c0e…","title":"Call dentist","notes":"","size":"S","energy":"low","context":"phone",
 "doDate":null,"dueDate":"2026-11-28","firstStep":"Find the number","parentId":null,
 "createdFrom":null,"status":"active","snoozedUntil":null,"completedAt":null,"droppedAt":null,
 "createdAt":"2026-11-22T18:00:00Z","updatedAt":"2026-11-22T18:00:00Z"}
```

## Steps

1. Enums and limits as module constants (`TITLE_MAX = 120`, …), reused by BE-082's CHECKs.
2. `TaskCreate`, `TaskUpdate`, `TaskOut`.
3. Tests.

## Tests

- `test_create_defaults_size_energy_context`
- `test_title_is_trimmed_and_required` (`"  "` → error)
- `test_title_longer_than_120_rejected`
- `test_unknown_size_rejected`
- `test_update_rejects_status_and_parent_id`
- `test_out_serialises_camel_case`

## Acceptance criteria

- [ ] Models are frozen; JSON is camelCase; Python is snake_case
- [ ] Every limit in the table is enforced
- [ ] `TaskUpdate` rejects `status` and `parentId`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "from app.tasks.schemas import TaskCreate as T; print(T(title='  Call dentist ').model_dump(by_alias=True)); T(title='x', size='XXL')"
```

The first print shows the trimmed title and defaults; the second call raises a `ValidationError` naming `size`.

## Review guide

1. Enums: values exactly as the table.
2. `TaskUpdate`: `extra="forbid"`, no status.
3. Limits live in constants, not repeated literals.

Things that should *not* be in the diff: SQLAlchemy, routes, recurrence.

## Out of scope

- Status rules → BE-081. Table → BE-082.
- `recurrenceRule` → deferred (later phase).

## Notes / log
