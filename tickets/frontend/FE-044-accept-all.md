# FE-044: Accept all

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5 · Milestone M7 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-034, BE-100 (BE-113 for the hand check)
- **Can run in parallel with:** FE-042, FE-043
- **Review size:** ~70 lines, 4 files, ~8 min

## Goal

The inbox header shows **Accept all (3)** when 3 items are confident enough, and one tap accepts them.

## Why this ticket exists

Closes M7. The count uses the same rule as the backend (`is_auto_acceptable`, BE-100), mirrored as a pure function.

## Read first

- `api/app/inbox/accept.py` (BE-100): the predicate to mirror.

## Design

- **Pattern:** Specification (mirrored pure predicate).

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/api/client.ts` (changed: `acceptAll(minConfidence = 0.8)`), `web/src/features/inbox/model/acceptAll.ts` + `.test.ts` (new: `AUTO_ACCEPT_THRESHOLD = 0.8`, `isAutoAcceptable(item, threshold)`, `autoAcceptableCount(items)`), `web/src/features/inbox/store/useInboxStore.ts` (changed: `acceptAll()` → reload after), `web/src/features/inbox/InboxScreen.tsx` (changed: header button).

- Button: outline, `CheckCheck` icon, label **Accept all (3)**; hidden when the count is 0; spinner while running.
- Toast: "3 added to your tasks." Failure: "Couldn't accept them. Nothing changed."

## Steps

1. Predicate + tests.
2. Client, store, button.

## Tests

- `isAutoAcceptable matches the backend rule at 0.8`
- `notes, expenses and fallback items are not counted`

## Acceptance criteria

- [ ] M7 demo: three confident items → Accept all → all three in `#tasks`
- [ ] Count matches what the server accepts
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Set `DUMP_PARSER=dev` in `api/.env` (BE-113) and restart the API. Press `/` and send `call dentist, also buy cat food, also water plants`: three confident items. Click **Accept all (3)** and compare with `#tasks`.

## Review guide

1. Threshold constant matches the backend default.

## Out of scope

- Changing the threshold in Settings → deferred.

## Notes / log
