# FE-005: Wire notification settings: store, optimistic save, rail entry

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** FE-004
- **Can run in parallel with:** none
- **Review size:** ~110 lines, 4 files, ~12 min

## Goal

The settings form opens from the app rail, loads from the API, and saves with an optimistic update that rolls back on failure.

## Why this ticket exists

This joins FE-003's client and FE-004's form. It follows the pattern FE-001 established for bills, so the reviewer is checking a known shape applied to a new feature.

## Read first

- `web/src/features/bills/store/useBillsStore.ts`: status values, optimistic update and rollback.
- `web/src/features/bills/model/transitions.ts`.
- `web/src/components/AppShell.tsx`: the rail.

## Design

- **Pattern:** State transitions as pure functions; optimistic update with rollback; a thin connected component.
- **Data flow:** open sheet → `load()` → `ready`; edit → local draft; Save → apply draft to `saved` → `PATCH` → success: server value; failure: restore previous + toast.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/notifications/store/useNotificationsStore.ts` (new) and its test.
- `web/src/features/notifications/components/NotificationSettingsSheet.tsx` (new): the connected component; renders `NotificationSettingsForm` inside the existing `Sheet`.
- `web/src/components/AppShell.tsx` (changed): a rail button `Notifications` that opens the sheet.

**Store**

```ts
interface State {
  readonly saved: NotificationSettings | null
  readonly status: 'idle' | 'loading' | 'ready' | 'saving' | 'error'
  load(): Promise<void>
  save(patch: NotificationSettingsPatch): Promise<void>
}
```

- `load`: `idle|error → loading → ready|error`. Called when the sheet opens; skipped when already `ready`.
- `save`: remember `previous = saved`; set `saved = {...saved, ...patch}`, `status = 'saving'`; call `patch`. Success → `saved = response`, `ready`. Failure → `saved = previous`, `ready`, and a `sonner` error toast `Couldn't save. Your settings are unchanged.` A `422` instead surfaces field errors to the form and shows no toast.
- The draft and `dirty` live in the sheet component's local state (`useState`), not the store: they are view state.
- Pause and resume call `save({ pausedUntil })` directly.
- The store takes the API as a parameter with `notificationsApi` as default, so tests pass a fake, as `useBillsStore.test.ts` does.

**Rail button.** Uses a `lucide-react` bell icon and the rail's existing button style; shows a small muted dot when `isPaused`. Keyboard-focusable; the sheet returns focus to it on close.

## Steps

1. Store with tests for each transition.
2. The sheet: draft state, `validateSettings`, `diffSettings`.
3. Rail button.
4. Browser check at both widths.

## Tests

- `load moves idle → loading → ready`
- `load failure sets error`
- `save applies the patch immediately`
- `save failure restores the previous settings`
- `save 422 keeps status ready and returns field errors`
- `pause sets pausedUntil through save`

## Acceptance criteria

- [ ] Opening the sheet shows saved values from the API
- [ ] A failed save restores the previous values and shows the toast
- [ ] The API key never appears in client code (requests go to `/api/...` through the proxy)
- [ ] Focus returns to the rail button when the sheet closes
- [ ] Checked in the browser at desktop and mobile widths
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With `make api-dev` and `make web-dev` running: open Notifications, change "From" to 21:00, Save, reload: it persists. Stop the API, change it again, Save: it rolls back with the toast.

## Review guide

Read the diff in this order, and check:

1. `save`: the three assignments of `saved` (optimistic, success, rollback).
2. The sheet: the draft is local; only `diffSettings` output is sent.
3. `AppShell.tsx`: one button added.

Things that should *not* be in the diff: a router or a settings page; caps UI.

## Out of scope

- Telegram status in the same sheet → FE-007.

## Assumptions

- Settings open in a sheet from the rail because the app has no router yet. A settings route can replace it when a second screen justifies adding one.

## Notes / log

The agent adds progress notes, decisions and open questions here.
