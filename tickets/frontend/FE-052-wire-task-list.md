# FE-052: Wire the task list and the Tasks screen

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4 · Milestone M3 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-032, FE-040, FE-051
- **Can run in parallel with:** M4 backend tickets
- **Review size:** ~130 lines, 5 files, ~12 min (store + screen; the store is small, so it isn't split)

## Goal

`#tasks` shows your real tasks from the API, and Done and Let go update the list instantly, rolling back with a calm toast if the API fails.

## Why this ticket exists

The M3 demo. Connects FE-051 to FE-032 through a small Zustand store, and replaces the dev fixture screen with the real one.

## Read first

- `web/src/features/bills/store/useBillsStore.ts`: store factory with injectable API, `LoadStatus`, optimistic update with rollback.
- `web/src/features/bills/model/transitions.ts`: pure transitions the store calls.

## Design

- **Pattern:** Connected component + reducer-style pure transitions + optimistic update with rollback.
- **Data flow:** `TasksScreen` → `useTasksStore.load()` → `tasksApi.listTasks()`; Done → `removeTask(state, id)` → `completeTask(id)` → on error restore previous list + `toast.error`.

## Packages

None new (`zustand`, `sonner` installed).

## Details

**Files:** `web/src/features/tasks/model/transitions.ts` (new: `removeTask`, `restoreTasks`), `web/src/features/tasks/store/useTasksStore.ts` (new), `web/src/features/tasks/store/useTasksStore.test.ts` (new), `web/src/features/tasks/TasksScreen.tsx` (new), `web/src/screens.tsx` (changed: add `tasks` with `ListChecks` icon, label **Tasks**; remove `dev-tasks`).

Store: `{ tasks, status, error, busyIds, load(), complete(id), drop(id) }`, created by `createTasksStore(api)`.

Toasts: Done → "Done." (no confetti, no streaks); Let go → "Let go. It's off your list." with **Undo** (calls `reopenTask`); failure → "Couldn't save that. It's back on your list."

## Steps

1. Pure transitions + tests.
2. Store + tests with a fake API.
3. Screen and registry entry; delete the dev entry.

## Tests

- `load sets ready with tasks`
- `complete removes optimistically and keeps it removed on success`
- `complete restores the task and exposes the error on failure`
- `drop then undo reopens the task`

## Acceptance criteria

- [ ] M3 demo works: `#tasks` lists M2 tasks grouped by date; Done and Let go persist across reload
- [ ] Killing the API then clicking Done restores the row with the calm toast
- [ ] `#dev-tasks` is gone
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make api-dev` + `make web-dev`, sign in, click **Tasks** in the rail. Complete one task, reload: it stays gone. Let go of another, press Undo: it's back. Stop the API, click Done: the row returns with the toast.

## Review guide

1. Transitions: pure, no mutation.
2. Store: rollback restores the exact previous list.
3. Toast wording: kind and neutral.

Things that should *not* be in the diff: new API functions.

## Out of scope

- Task detail, editing, subtasks UI → later phase.

## Notes / log
