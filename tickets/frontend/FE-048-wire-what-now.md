# FE-048: Wire What now?: #now, the n shortcut, rerolls

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 stories 9–10, 12 · Milestone M10 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-035, FE-040, FE-046, FE-047
- **Can run in parallel with:** BE-107, BE-108
- **Review size:** ~120 lines, 4 files, ~12 min

## Goal

`#now` (or `n` anywhere) runs the whole flow: questions → one card → Another (at most 3, then a break) → Not today → next pick.

## Why this ticket exists

The M10 demo. Flow state lives in a pure reducer so the reroll limit and transitions are tested without a browser.

## Read first

- `web/src/features/bills/model/transitions.ts`: pure transitions.
- `web/src/lib/shortcut.ts` (FE-035).

## Design

- **Pattern:** State transitions (reducer): `nowReducer(state, event) → state`; the screen performs the API calls the reducer asks for.

## Packages

None new.

## Details

**Files:** `web/src/features/now/model/flow.ts` + `.test.ts` (new), `web/src/features/now/NowScreen.tsx` (new), `web/src/screens.tsx` (changed: `now` entry with `Compass` icon, label **What now?**; remove `dev-now`), `web/src/App.tsx` (changed: `useShortcut('n', () => location.hash = '#now')`).

```ts
type NowState =
  | { step: 'asking' }
  | { step: 'loading'; rerolls: number }
  | { step: 'showing'; result: NowResult; rerolls: number }
  | { step: 'break' } | { step: 'nothing-fits' } | { step: 'error'; message: string }
```

- Another: `recordAction(id, 'rerolled')`, then `askNow` again (the reroll is now a recent skip server-side); after the third reroll → `break`.
- Not today: `recordAction(id, 'not-today')` → toast "Okay, it's off today's list." → `askNow` again (rerolls not counted).
- Start: `recordAction(id, 'started')`, then a placeholder toast "Focus timer comes next." (FE-050 replaces it).
- Errors: calm message + **Try again**.

## Steps

1. Reducer + tests.
2. Screen.
3. Registry entry and shortcut.

## Tests

- `three rerolls lead to break`
- `not today does not count as a reroll`
- `empty result leads to nothing-fits`
- `ask again from break resets rerolls`

## Acceptance criteria

- [ ] M10 demo: `n` → chips → card; Another ×3 → break; Not today → task snoozed (check `#tasks`)
- [ ] `n` doesn't fire while typing
- [ ] `#dev-now` removed
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With a few tasks: press `n`, choose Low + 15, Show me. Press Another three times → break card. Ask again, press Not today → toast; `#tasks` no longer lists that task today.

## Review guide

1. All flow rules in `flow.ts`.
2. One API call per user action.

## Out of scope

- Focus timer → FE-050.

## Notes / log
