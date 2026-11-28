# FE-037: Wire Quick add: the / shortcut, POST /inbox/dumps and a toast

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 4, §5.1 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-033, FE-035, FE-036
- **Can run in parallel with:** FE-038, FE-039
- **Review size:** ~80 lines, 3 files, ~8 min

## Goal

Pressing `/` anywhere (or the rail's Quick add button) opens Quick add; saving posts the dump and shows a short toast.

## Why this ticket exists

Joins the dialog (FE-036) to the API (FE-033) with the shortcut (FE-035). After this, capture works from any screen.

## Read first

- `web/src/App.tsx` and `web/src/components/AppShell.tsx`: where global UI mounts.
- `sonner` usage in the bills feature.

## Design

- **Pattern:** Connected component (`QuickAddContainer` owns open/value/status; the dialog stays presentational).

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/QuickAddContainer.tsx` (new), `web/src/App.tsx` (changed: mount it inside the signed-in app), `web/src/components/AppShell.tsx` (changed: optional `actions` slot in the rail for a **Quick add** ghost button with a `/` kbd hint).

- On submit: `status = 'sending'` → `inboxApi.postDump(value)` → close, clear, toast.
- Toast copy: parsed → "In your inbox · 3 items" with **View** (`#inbox`); not parsed → "Saved to your inbox as is." with **View**.
- On error: `status = 'error'`, message from `ApiError`, text kept. 401/403 are already handled globally.

## Steps

1. Container.
2. Mount + rail button.

## Tests

- Pure `toastFor(result)` in `web/src/features/inbox/model/quickAdd.ts`: `one item says item`, `parsed false says as is`.

## Acceptance criteria

- [ ] `/` opens Quick add from Bills, Tasks and Playground; typing `/` inside a field doesn't
- [ ] Saving shows the toast and the dump is in `GET /inbox`
- [ ] Failure keeps the text and shows the error
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make api-dev` + `make web-dev`: on Bills press `/`, type two lines, ⌘↵ → toast. Check `GET /inbox` in `/docs`. Stop the API and try again → error, text still there.

## Review guide

1. Container: the only stateful piece; dialog untouched.
2. Toast copy: calm.

## Out of scope

- The Inbox screen → FE-041.

## Notes / log
