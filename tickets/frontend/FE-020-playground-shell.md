# FE-020: Playground shell: tabs and the 'off' and 'not an admin' states

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-019
- **Can run in parallel with:** BE-065 to BE-079
- **Review size:** ~90 lines, 3 files plus tests, ~12 min

## Goal

The playground screen has a header, four tabs (Updates, Explain, Templates, Test message) with placeholder bodies, and clear full-screen states for loading, switched off, not an admin and error. It is presentational: the gate state comes in as a prop.

## Why this ticket exists

Every tool panel plugs into this frame. Building the frame and its gate states first, fed by a prop, lets them be reviewed in the browser without any backend. FE-021 connects the real probe.

## Read first

- `web/src/features/auth/NotAllowedScreen.tsx` and `web/src/features/bills/components/LoadStates.tsx`: how full-area states are built here.
- `DESIGN.md`: Typography, Cards / Containers, Navigation, Do's and Don'ts.
- `web/src/components/ui/`: check whether a tabs primitive exists; if not, add shadcn's with `npx shadcn add tabs` (it is on Base UI, already installed).

## Design

- **Pattern:** Presentational component driven by a pure gate function.
- **Data flow:** `gate` prop → `PlaygroundShell` → one of five views; `ready` shows the tabs.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/gate.ts` (new): `type PlaygroundGate = 'loading' | 'ready' | 'off' | 'not-admin' | 'error'`; `gateFromProbe(result: { ok: true } | { ok: false; status: number }): PlaygroundGate` (pure): ok → `ready`; `404` → `off`; `403` → `not-admin`; anything else → `error`.
- `web/src/features/playground/PlaygroundShell.tsx` (new): props `{ gate: PlaygroundGate; onRetry: () => void; panels?: Partial<Record<TabId, ReactNode>> }`.
  - `ready`: title 'Telegram playground' in `label-caps`, one line 'Development only. Nothing here reaches anyone but you.', then the tabs. A tab without a panel shows 'Coming soon'.
  - `off`: 'The playground is switched off', with the variable name `TELEGRAM_PLAYGROUND_ENABLED` in a code style and one line on where to set it.
  - `not-admin`: 'This area is for admins.'
  - `error`: 'Can't load the playground.' with **Try again**.
  - `loading`: a calm skeleton, `role="status"`.
- `web/src/App.tsx` (changed): the playground screen renders `<PlaygroundShell gate="ready" … />` for now.
- `web/src/features/playground/gate.test.ts` (new).

States to polish: loading, empty, error, hover, focus-visible, disabled, phone width, light and dark. Use the tokens and type scale in `DESIGN.md`; this is an internal tool, but not an unstyled one. Tabs must work with arrow keys and show a visible focus ring; on phone width they scroll horizontally without the page scrolling.

## Steps

1. `gateFromProbe` and tests.
2. The shell with all five views.
3. Render it from `App`.
4. Look at each view by changing the prop.

## Tests

- `test_ok_is_ready`.
- `test_404_is_off`.
- `test_403_is_not_admin`.
- `test_other_statuses_and_network_error_are_error`: `0`, `500`.

## Acceptance criteria

- [ ] The shell renders all five gate views from a prop
- [ ] Four tabs exist, keyboard-navigable, with 'Coming soon' bodies
- [ ] The 'off' view names the variable to set and no value
- [ ] No network call is made by this ticket
- [ ] Checked in the browser at desktop and phone width, in light and dark
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. As admin open `#playground`: the tabs show.
2. Temporarily pass each gate value in `App.tsx` and look at each view at 375 px and in dark mode. Restore `ready`.

## Review guide

Read the diff in this order, and check:

1. `gate.ts`: pure, with every status mapped?
2. `PlaygroundShell.tsx`: any data fetching? There should be none.
3. Compare the views with `DESIGN.md`.

Things that should *not* be in the diff: API calls, tool panels, stores.

## Out of scope

- The real probe and client → FE-021.
- Tool panels → FE-023, FE-025, FE-027, FE-029.

## Notes / log

The agent adds progress notes, decisions and open questions here.
