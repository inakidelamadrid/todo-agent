# FE-014: Account control with sign-out in the app shell

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.1 Sign-in and sign-out (signed-in state)
- **Assigned agent / harness / model:**
- **Depends on:** FE-010
- **Can run in parallel with:** FE-012, FE-013
- **Review size:** ~80 lines, 4 files plus tests, ~12 min

## Goal

Signed in, the shell shows the owner's name or email and a **Sign out** action; signing out returns to the sign-in screen.

## Why this ticket exists

Without it there is no way to leave a shared machine's session. The label rule (name, else email, else a neutral word) is a pure function, so only the thin component needs a look in the browser.

## Read first

- `web/src/components/AppShell.tsx`: the rail layout, including the phone (horizontal) and desktop (vertical) variants.
- `DESIGN.md`: Navigation and Buttons.
- Clerk docs (https://clerk.com/docs/references/react/overview): `useUser`, `useClerk().signOut`.

## Design

- **Pattern:** Presentational component with a pure formatting function (`accountLabel`).
- **Data flow:** `useUser()` → `accountLabel(user)` → `AccountControl` → `signOut()` → `AuthGate` sees signed-out.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/auth/accountLabel.ts` (new): `accountLabel(user: { fullName?: string | null; primaryEmail?: string | null } | null | undefined): string`: trimmed full name, else email, else `'Account'`.
- `web/src/features/auth/AccountControl.tsx` (new): shows the label (truncated with a title tooltip) and a **Sign out** button with the `LogOut` icon from `lucide-react`. States: default, hover, focus-visible, **signing out** (disabled, label 'Signing out…'), error (a toast 'Couldn't sign out. Try again.' with `sonner`).
- `web/src/components/AppShell.tsx` (changed): a new optional `account` slot, rendered at the bottom of the desktop rail and, on phone width, as an icon-only button at the end of the top bar.
- `web/src/App.tsx` (changed): passes `<AccountControl />` as `account`.
- `web/src/features/auth/accountLabel.test.ts` (new).

## Steps

1. Write `accountLabel` and its tests.
2. Build the control with all states.
3. Add the slot to the shell and pass it.
4. Check desktop and phone, light and dark.

## Tests

- `test_prefers_full_name`.
- `test_falls_back_to_email`.
- `test_falls_back_to_account`: null, undefined and blank values.
- `test_trims_whitespace`.

## Acceptance criteria

- [ ] The shell shows the owner's name or email and a **Sign out** action when signed in
- [ ] Signing out shows the sign-in screen, and the bills data is not visible
- [ ] The control has default, hover, focus, signing-out and error states
- [ ] It works at phone width (icon only) and with the keyboard
- [ ] Tests and the build pass
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-dev`, signed in: the control shows in the rail. Click **Sign out**: the sign-in screen shows.
2. Resize to 375 px: the control is an icon in the top bar; it opens or acts with the keyboard (Enter and Space).
3. Tab to it: the focus ring is visible.

## Review guide

Read the diff in this order, and check:

1. `AppShell.tsx`: is the slot optional so nothing else breaks?
2. `AccountControl.tsx`: are all states handled, and is the sign-out error surfaced?

Things that should *not* be in the diff: A profile page, account settings, `UserButton` from Clerk.

## Out of scope

- Handling an expired session on a request → FE-015.

## Notes / log

The agent adds progress notes, decisions and open questions here.
