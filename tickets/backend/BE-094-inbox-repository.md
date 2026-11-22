# BE-094: Inbox repository: save a dump, list new items, get one

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-092, BE-093
- **Can run in parallel with:** M2 tickets
- **Public endpoint?** no
- **Review size:** ~80 lines, 2 files, ~8 min

## Goal

`save_dump`, `list_inbox` and `get_item` persist and read dumps and their items.

## Why this ticket exists

The two routes in M4 (BE-095, BE-096) need exactly these three operations; status changes come later with triage.

## Read first

- `api/app/bills/repository.py`.

## Design

- **Pattern:** Repository.

## Packages

None new.

## Details

**Files:** `api/app/inbox/repository.py` (new), `api/tests/test_inbox_repository.py` (new).

```python
async def save_dump(session, data: DumpIn, drafts: Sequence[ItemDraft]) -> tuple[Dump, list[InboxItem]]
async def list_inbox(session, now: datetime) -> list[tuple[InboxItem, str]]   # (item, dump raw_text)
async def get_item(session, item_id: UUID) -> tuple[InboxItem, str] | None
```

- `save_dump`: one dump + N items in the same transaction; `payload` stored as `draft.payload.model_dump(mode="json", by_alias=True)`.
- `list_inbox`: items with `status = 'new'`, or `status = 'snoozed' AND snoozed_until <= now`; newest first (`created_at DESC, id`); joined to `dumps` for `raw_text`.

## Steps

1. Three functions.
2. Tests.

## Tests

- `test_save_dump_writes_dump_and_items`
- `test_list_inbox_newest_first`
- `test_list_inbox_hides_snoozed_until_due`
- `test_list_inbox_hides_accepted_and_discarded`
- `test_get_item_missing_returns_none`

## Acceptance criteria

- [ ] No HTTP imports
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run pytest -k inbox_repository -v
```

## Review guide

1. `save_dump`: single flush, payload stored camelCase.
2. `list_inbox`: snoozed items reappear exactly when due.

Things that should *not* be in the diff: status updates (BE-098/099).

## Out of scope

- Accept/discard/snooze writes → BE-098, BE-099.

## Notes / log
