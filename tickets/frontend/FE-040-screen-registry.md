# FE-040: Data-driven screen registry (refactor, no behaviour change)

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §6 · Milestone M3 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** every backend ticket, FE-035, FE-036, FE-049
- **Review size:** ~70 lines, 3 files, ~8 min

## Goal

Screens are declared once in a registry (id, label, icon, admin-only, dev-only, component), and `App.tsx` builds the nav and picks the screen from it. Bills and Playground behave exactly as today.

## Why this ticket exists

EPIC-003 adds three screens (`#tasks`, `#inbox`, `#now`) plus temporary dev-only fixture screens for presentational tickets. Today `screen.ts` and `App.tsx` hard-code two screens with `if`s; adding five more that way would grow both files every ticket. This refactor makes each later screen a one-line registry entry.

## Read first

- `web/src/lib/screen.ts` and `screen.test.ts`: `resolveScreen`, `useHashScreen`.
- `web/src/App.tsx`: `navItems`, `SignedInApp`.

## Design

- **Pattern:** Strategy: a `Record` from screen id to its definition instead of `if` chains.

## Packages

None new.

## Details

**Files:** `web/src/lib/screen.ts` (changed), `web/src/lib/screen.test.ts` (changed), `web/src/App.tsx` (changed), `web/src/screens.tsx` (new: the registry with its React components).

```ts
export interface ScreenDef {
  readonly id: string
  readonly label: string
  readonly icon: ReactNode
  readonly adminOnly?: boolean
  readonly devOnly?: boolean       // shown only when import.meta.env.DEV; never in nav
  readonly render: () => ReactNode
}

/** Pure: the hash's screen if visible to this user, else the first (default) screen. */
export const resolveScreen = (hash: string, defs: readonly ScreenDef[], ctx: { isAdmin: boolean; isDev: boolean }): ScreenDef
export const visibleNav = (defs, ctx, current: string): readonly NavItem[]   // excludes devOnly
```

The registry lists `bills` (default) and `playground` (`adminOnly`). Dev-only fixture screens are reached by typing `#dev-<name>`; they never appear in the nav and are excluded from production builds by the `isDev` check.

## Steps

1. Move the two screens into `screens.tsx`.
2. Generalise `resolveScreen` and add `visibleNav`.
3. Update tests; keep the old cases passing.

## Tests

- existing `screen.test.ts` cases, rewritten against the registry
- `hides admin screens from non-admins`
- `dev-only screens resolve only in dev and never appear in nav`
- `unknown hash falls back to bills`

## Acceptance criteria

- [ ] Bills and Playground switch exactly as before, for admin and non-admin
- [ ] Adding a screen means adding one registry entry
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make web-dev`: click Bills and Playground (as admin), use Back/Forward, type `#playground` as non-admin → Bills. Nothing looks different.

## Review guide

1. `resolveScreen`: pure; same fallback as before.
2. `App.tsx`: no screen-specific `if` left.

Things that should *not* be in the diff: new screens.

## Out of scope

- `#tasks` → FE-052; `#inbox` → FE-041; `#now` → FE-048.

## Notes / log
