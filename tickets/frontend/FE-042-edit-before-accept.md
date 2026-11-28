# FE-042: Edit an item before accepting

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5, §5.4 · Milestone M7 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-034
- **Can run in parallel with:** FE-043, FE-044
- **Review size:** ~150 lines, 4 files, ~14 min

## Goal

**Edit** on a card opens a sheet prefilled with what the AI parsed; saving accepts the item with your edits.

## Why this ticket exists

Parsing will sometimes be wrong; fixing it should take seconds, not a separate edit after accepting. Uses BE-098's `TaskEdits`.

## Read first

- `web/src/features/bills/components/BillFormSheet.tsx`: the house form sheet (fields, validation, field errors from `ApiError`).
- `DESIGN.md`: Inputs / Fields, Sheet shadow.

## Design

- **Pattern:** Compound components (`Sheet`, `SheetContent`, …) + pure form model.

## Packages

None new (form state stays hand-rolled like `BillFormSheet`; seven fields don't justify a form library).

## Details

**Files:** `web/src/features/inbox/components/EditItemSheet.tsx` (new), `web/src/features/inbox/model/editForm.ts` + `.test.ts` (new), `web/src/features/inbox/InboxScreen.tsx` (changed: `onEdit`).

Fields: **Title** (1–120), **Size** (select XS–XL with `SIZE_LABEL`), **Energy** (low/medium/high), **Context** (five options), **Planned for** (date), **Due** (date), **First step** (0–200). Prefill from the payload (reminder → due date).

- `formFromItem(item) → EditForm`, `validate(form) → FieldErrors`, `toEdits(form, item) → Partial<TaskInput>` (only changed fields) — all pure.
- Submit label **Accept with changes** (primary scarlet, the sheet's only one). Esc closes without saving. Server `422` field errors show under their fields.
- Phone: sheet full-width from the bottom; inputs 44px tall.

## Steps

1. Form model + tests.
2. Sheet.
3. Wire `onEdit` → open → `accept(id, edits)`.

## Tests

- `formFromItem prefills a reminder's due date`
- `validate requires a title and limits lengths`
- `toEdits sends only changed fields`

## Acceptance criteria

- [ ] Edit → change title and size → Accept with changes → the task in `#tasks` has the new values
- [ ] Keyboard-only works; focus returns to the card on close
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Capture "call dentist", Edit → set size M, context phone, due Friday → Accept with changes → check `#tasks`.

## Review guide

1. Form logic in `editForm.ts`, not the component.
2. Only changed fields are sent.

## Out of scope

- Editing tasks after they're accepted → later phase.

## Notes / log
