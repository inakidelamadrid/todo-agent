# FE-043: Snooze an inbox item

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3 · Milestone M7 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-034, BE-099
- **Can run in parallel with:** FE-042, FE-044
- **Review size:** ~100 lines, 4 files, ~10 min

## Goal

**Snooze** on a card opens a small popover (Later today · Tomorrow · Next week · Pick a date); choosing one hides the item until then.

## Why this ticket exists

Snooze is the "not now" for the inbox, always one tap (epic §2). Backend rules are in BE-099; this adds the client call and the popover.

## Read first

- `web/src/features/bills/components/MarkPaidPopover.tsx`: popover pattern, focus handling.

## Design

- **Pattern:** Presentational popover + optimistic store action (reuses FE-034's transitions).

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/api/client.ts` (changed: `snoozeItem(id, option, date?)`), `web/src/features/inbox/components/SnoozePopover.tsx` (new), `web/src/features/inbox/store/useInboxStore.ts` (changed: `snooze`), `web/src/features/inbox/InboxScreen.tsx` (changed: `onSnooze`).

- Options as a vertical list of ghost buttons, each with the resolved time in muted text ("Tomorrow · 8:00").
- **Pick a date** reveals a date input (min = tomorrow) and a **Snooze** outline button.
- Toast: "Snoozed until tomorrow." Failure rolls back.
- Keyboard: arrow keys move through options; Enter picks; Esc closes.

## Steps

1. Client + test.
2. Popover.
3. Store action + test, wiring.

## Tests

- `snoozeItem sends option and date`
- `snooze rolls back on failure`
- Pure `optionHint(option, now)` → "Tomorrow · 8:00": `hints use Mexico City time`

## Acceptance criteria

- [ ] Snooze → item leaves the list; after its time it's back (check with `later-today` against a backend clock override, or by waiting)
- [ ] Keyboard-only works
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Snooze an item to Tomorrow → gone; `GET /inbox` in `/docs` doesn't show it; the DB row has `status = snoozed` and tomorrow 14:00 UTC.

## Review guide

1. Popover focus handling matches `MarkPaidPopover`.

## Out of scope

- Snoozing tasks from the task list → later.

## Notes / log
