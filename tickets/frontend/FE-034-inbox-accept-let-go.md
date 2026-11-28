# FE-034: Accept and Let go in the Inbox

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5 · Milestone M6 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-033, FE-041, BE-098
- **Can run in parallel with:** BE-099, BE-100
- **Review size:** ~140 lines, 5 files, ~12 min

## Goal

Accept and Let go on an inbox card act instantly, persist through the API, and roll back with a calm message if the API fails.

## Why this ticket exists

The M6 demo: the inbox becomes a triage tool. Optimistic updates make it feel immediate, which is what keeps triage under a minute.

## Read first

- `web/src/features/bills/store/useBillsStore.ts`: optimistic update with rollback.
- `web/src/features/tasks/model/transitions.ts` (FE-052): same transition style.

## Design

- **Pattern:** Optimistic update with rollback; pure transitions (`removeItem`, `restoreItems`) called by the store.

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/api/client.ts` (changed: `acceptItem(id, edits?)`, `discardItem(id)`), `web/src/features/inbox/model/transitions.ts` + `.test.ts` (new), `web/src/features/inbox/store/useInboxStore.ts` + `.test.ts` (changed: `accept(id, edits?)`, `letGo(id)`, `busyIds`), `web/src/features/inbox/InboxScreen.tsx` (changed: pass `onAccept` / `onLetGo` to cards).

- Accept: remove → `acceptItem` → toast "Added to your tasks." with **View** (`#tasks`) | rollback + toast "Couldn't accept that. It's back in your inbox."
- Let go: remove → `discardItem` → toast "Let go." | rollback.
- A `409` (already handled elsewhere) removes the item without an error toast and reloads the list.

## Steps

1. Client functions + tests.
2. Transitions + tests.
3. Store actions + tests.
4. Screen wiring.

## Tests

- `acceptItem posts edits when given`
- `removeItem and restoreItems are pure`
- `accept rolls back on failure`
- `409 reloads instead of rolling back`

## Acceptance criteria

- [ ] M6 demo: accept → item leaves the inbox and appears in `#tasks`; Let go → gone after reload
- [ ] API down → card returns with the calm toast
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Capture "buy cat food" with `/`, go to `#inbox`, Accept → toast, click View → it's in Tasks. Capture another, Let go, reload → gone. Stop the API, Accept → card comes back.

## Review guide

1. Rollback restores the exact previous list.
2. Copy is kind.

## Out of scope

- Edit before accept → FE-042; snooze → FE-043; accept all → FE-044.

## Notes / log
