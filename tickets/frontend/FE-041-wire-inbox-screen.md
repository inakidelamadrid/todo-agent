# FE-041: Wire the Inbox screen (read-only)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-033, FE-039, FE-040
- **Can run in parallel with:** FE-037
- **Review size:** ~80 lines, 4 files, ~8 min

## Goal

`#inbox` shows your real untriaged items, refreshed after every Quick add.

## Why this ticket exists

The M5 demo: capture from anywhere, see it land. Read-only on purpose; actions come in M6.

## Read first

- `web/src/features/bills/store/useBillsStore.ts`: store factory and load status.

## Design

- **Pattern:** Connected component + small Zustand store.

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/store/useInboxStore.ts` + `.test.ts` (new: `{ items, status, error, load() }` via `createInboxStore(api)`), `web/src/features/inbox/InboxScreen.tsx` (new), `web/src/features/inbox/QuickAddContainer.tsx` (changed: call `useInboxStore.getState().load()` after a successful dump), `web/src/screens.tsx` (changed: `inbox` entry, `Inbox` icon, label **Inbox**; remove `dev-inbox`).

The nav label never shows a count badge (no red counters).

## Steps

1. Store + tests.
2. Screen + registry entry.
3. Refresh after Quick add.

## Tests

- `load sets items and ready`
- `load failure sets error`

## Acceptance criteria

- [ ] M5 demo: `/`, type, save → the item appears in `#inbox` without a reload
- [ ] Empty DB shows inbox zero
- [ ] `#dev-inbox` removed
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Open `#inbox`, press `/`, capture "buy cat food", save: the card appears with "You said: “buy cat food”".

## Review guide

1. Store: load only; no actions yet.

## Out of scope

- Accept / Let go → FE-034.

## Notes / log
