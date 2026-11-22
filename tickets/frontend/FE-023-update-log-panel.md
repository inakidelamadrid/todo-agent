# FE-023: Update log panel (presentational, all states)

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-020
- **Can run in parallel with:** FE-021, FE-022, FE-025, FE-027
- **Review size:** ~100 lines, 2 files plus tests, ~12 min

## Goal

A panel shows a list of updates (time, kind, route, status, a 'playground' mark) with status and route filters, from props, in every state.

## Why this ticket exists

One presentational component per ticket, fed by fixture data, so its states can be reviewed without a backend. FE-024 connects it.

## Read first

- `web/src/features/bills/components/BillTable.tsx` and `LoadStates.tsx`: table and state patterns.
- `DESIGN.md`: Status tags, Typography (tabular figures for times).
- `UpdateLogItem` in FE-021's ticket (declare the type locally if FE-021 is not merged).

## Design

- **Pattern:** Presentational component plus a pure formatting function.
- **Data flow:** props `{ items, status, filters, onFiltersChange, onRefresh }` → table.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/components/UpdateLogPanel.tsx` (new).
- `web/src/features/playground/updateLog.ts` (new): `statusTone(status): 'neutral' | 'good' | 'bad'` and `formatReceivedAt(iso: string, now: Date): string` ('just now', '5 min ago', then a date and time in America/Mexico_City via `Intl.DateTimeFormat`). Both pure.
- `web/src/features/playground/updateLog.test.ts` (new).

**Columns:** received, kind, route (monospace), status (tag), and a small 'playground' tag when `playground` is true.

**States:** loading (skeleton rows), empty ('No updates yet. Send your dev bot a message.'), error (message plus **Try again**), loaded; filter controls (status select, route text input) and a **Refresh** button; disabled controls while loading. Phone width: the table becomes stacked rows. No message content is ever shown, because none is ever received.

States to polish: loading, empty, error, hover, focus-visible, disabled, phone width, light and dark. Use the tokens and type scale in `DESIGN.md`; this is an internal tool, but not an unstyled one.

## Steps

1. The two pure functions with tests.
2. The panel with fixture data for each state.
3. Show it in the Updates tab with fixtures.
4. Check every state in the browser.

## Tests

- `test_status_tone`: processed → good, failed → bad, received → neutral.
- `test_format_received_at_relative_and_absolute`.
- `test_format_received_at_uses_mexico_city_time`.

## Acceptance criteria

- [ ] The panel renders loading, empty, error and loaded states from props
- [ ] Playground-made rows are marked
- [ ] Filters and refresh call their callbacks; nothing fetches
- [ ] Readable at 375 px, keyboard-usable, both themes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Open the Updates tab with the fixture: rows show. Switch the fixture state to each of the four and look, at 375 px and in dark mode.

## Review guide

Read the diff in this order, and check:

1. Is the component free of fetching and stores?
2. Are times formatted in one pure function?

Things that should *not* be in the diff: API calls, a store.

## Out of scope

- Wiring → FE-024.

## Notes / log

The agent adds progress notes, decisions and open questions here.
