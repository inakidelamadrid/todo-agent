# FE-024: Wire the update log to the API

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-021, FE-023
- **Can run in parallel with:** FE-025 to FE-029
- **Review size:** ~60 lines, 3 files plus tests, ~10 min

## Goal

The Updates tab loads real updates, applies the filters, and refreshes on demand.

## Why this ticket exists

The first tool that works end to end. Small, because the panel and the client already exist.

## Read first

- `web/src/features/bills/store/useBillsStore.ts`: load status and error handling.
- `UpdateLogPanel` (FE-023), `createPlaygroundApi` (FE-021).

## Design

- **Pattern:** Small Zustand store with explicit status; the component stays presentational.
- **Data flow:** tab opens → `useUpdateLogStore.load(filters)` → `listUpdates` → `{ items, status }` → panel.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/useUpdateLogStore.ts` (new): `{ items; status: 'idle' | 'loading' | 'ready' | 'error'; filters; load(filters?): Promise<void> }`. A newer `load` wins over an older one still in flight (ignore stale responses).
- `web/src/features/playground/UpdatesTab.tsx` (new): connects store and panel; loads on first show.
- The shell usage (changed): pass `UpdatesTab` as the `updates` panel.
- `web/src/features/playground/useUpdateLogStore.test.ts` (new).

Route filter input is debounced by 300 ms before calling `load`.

## Steps

1. Store with tests.
2. Tab component.
3. Plug into the shell.
4. Check with the dev bot.

## Tests

- `test_load_sets_items_and_ready`.
- `test_load_error_sets_error_and_keeps_old_items`.
- `test_stale_response_is_ignored`.
- `test_filters_are_passed_to_the_client`.

## Acceptance criteria

- [ ] Opening the tab lists real updates, newest first
- [ ] Filters and **Refresh** reload the list
- [ ] An error shows the error state with a working **Try again**
- [ ] A slow earlier request cannot overwrite a newer result
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Send the dev bot `/help`, open the Updates tab: the row appears with route `core.help`. Filter by status `failed`: empty state.

## Review guide

Read the diff in this order, and check:

1. The store: how are stale responses ignored?
2. Is the panel still purely presentational?

Things that should *not* be in the diff: Auto-refresh or polling, pagination.

## Out of scope

- Auto-refresh → not planned.

## Notes / log

The agent adds progress notes, decisions and open questions here.
