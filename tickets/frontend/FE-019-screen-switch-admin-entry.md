# FE-019: Screen switch from the URL hash, and an admin-only rail entry

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-018
- **Can run in parallel with:** BE-065 to BE-079
- **Review size:** ~70 lines, 4 files plus tests, ~12 min

## Goal

The app can show a second screen. `#playground` shows a placeholder playground for admins; everyone else, and every other hash, sees Bills. The rail shows a **Playground** entry to admins only.

## Why this ticket exists

The app has one screen and no router. A second screen needs the smallest possible switch; a router library is not worth it for two destinations, so the decision is a pure function of the hash and the admin flag. The placeholder is replaced by FE-020.

## Read first

- `web/src/App.tsx` and `web/src/components/AppShell.tsx`: the rail's single hard-coded Bills link.
- `web/src/features/auth/authView.ts`: a pure 'which view' function to imitate.
- `DESIGN.md`: Navigation.

## Design

- **Pattern:** State as a pure function (`resolveScreen`), with one small hook at the edge listening to `hashchange`.
- **Data flow:** `window.location.hash` → `useHashScreen()` → `resolveScreen(hash, isAdmin)` → `'bills' | 'playground'` → `App` renders it.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/lib/screen.ts` (new): `type Screen = 'bills' | 'playground'`; `resolveScreen(hash: string, isAdmin: boolean): Screen` (pure): `'#playground'` and admin → `'playground'`; anything else → `'bills'`. `useHashScreen(isAdmin)`: subscribes to `hashchange`, returns the screen.
- `web/src/components/AppShell.tsx` (changed): the nav takes `items: readonly { href: string; label: string; icon: ReactNode; current: boolean }[]` instead of the hard-coded link. Styling of an item is unchanged; `aria-current="page"` on the current one.
- `web/src/App.tsx` (changed): builds the items (Bills always; Playground with the `FlaskConical` icon from `lucide-react` only when `isAdmin`), renders `BillsMonthView` or a placeholder `<p>` for the playground.
- `web/src/lib/screen.test.ts` (new).

Hand-written instead of a package: a router (`react-router`) would be heavier than this twenty-line function for two screens. Revisit when a third screen arrives.

States: hover and focus-visible on both entries, current-page marker, phone width (the rail is a top bar there; both entries must fit).

## Steps

1. `resolveScreen` and tests.
2. Generalise the shell's nav (no visual change for Bills).
3. Switch in `App`.
4. Check as admin and as non-admin.

## Tests

- `test_playground_hash_for_admin_is_playground`.
- `test_playground_hash_for_non_admin_is_bills`.
- `test_empty_bills_and_unknown_hashes_are_bills`.

## Acceptance criteria

- [ ] An admin sees a **Playground** rail entry and reaches the placeholder at `#playground`
- [ ] A non-admin sees no entry, and `#playground` typed by hand shows Bills
- [ ] The Bills screen looks and behaves exactly as before
- [ ] Back and forward buttons switch screens
- [ ] Checked in the browser at desktop and phone width, in light and dark
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. As admin: the entry shows; click it → placeholder; Back → Bills.
2. Remove yourself from `ADMIN_USER_IDS`, restart the API, reload: no entry; `#playground` shows Bills.

## Review guide

Read the diff in this order, and check:

1. `screen.ts`: is the decision pure and the listener the only side effect?
2. `AppShell.tsx`: did Bills' markup change beyond coming from a list?

Things that should *not* be in the diff: The playground UI, a router dependency, calls to playground endpoints.

## Out of scope

- The playground shell → FE-020.

## Notes / log

The agent adds progress notes, decisions and open questions here.
