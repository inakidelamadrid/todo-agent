# FE-016: A `403` shows a clear 'not allowed' screen with sign-out

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.2 Session handling, §5.4 Owner allowlist
- **Assigned agent / harness / model:**
- **Depends on:** FE-015
- **Can run in parallel with:** none
- **Review size:** ~60 lines, 5 files plus tests, ~12 min

## Goal

If a non-owner Clerk account gets `403` from the API, the app shows 'This account isn't allowed to use todo-agent' with a **Sign out** button, and does not loop.

## Why this ticket exists

The API allowlist is the real gate (BE-062). If a stranger somehow gets a Clerk session, they must see a plain explanation and a way out instead of an app full of errors.

## Read first

- `web/src/features/auth/authFailure.ts` and `authView.ts` (FE-015, FE-010).
- `web/src/features/bills/store/`: how a small Zustand store is written here.

## Design

- **Pattern:** Small store for one flag, and the pure view function extended with one more input.
- **Data flow:** response `403` → `handleAuthFailure(403)` → `authStore.setForbidden()` → `resolveAuthView(... forbidden)` → `forbidden` view → `NotAllowedScreen`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/auth/authStore.ts` (new): Zustand store `{ forbidden: boolean; setForbidden: () => void; reset: () => void }`.
- `web/src/features/auth/authView.ts` (changed): `AuthView` gains `'forbidden'`; the input gains `forbidden: boolean`; priority: `error` → `loading` → (signed in and `forbidden`) → `forbidden` → `signed-in` / `signed-out`. Signing out resets the flag.
- `web/src/features/auth/NotAllowedScreen.tsx` (new): same layout family as the sign-in screen; text 'This account isn't allowed to use todo-agent.'; one **Sign out** button (states: default, hover, focus, signing out). Calm wording.
- `web/src/features/auth/authFailure.ts` (changed): the `forbidden` branch calls `setForbidden()`.
- `web/src/features/auth/AuthGate.tsx` (changed): handle the new view; call `reset()` on sign-out.
- Tests: `authView.test.ts` (changed), `authStore.test.ts` (new).

No loop: the screen replaces the app, so no more API calls are made until the user signs out.

## Steps

1. Add the store and extend `resolveAuthView` with tests.
2. Build the screen.
3. Fill the `forbidden` branch and wire the gate.
4. Check by hand with a second Google account.

## Tests

- `test_signed_in_and_forbidden_is_forbidden`.
- `test_forbidden_flag_ignored_when_signed_out`.
- `test_error_and_loading_still_take_priority`.
- `test_store_set_and_reset`.

## Acceptance criteria

- [ ] A `403` shows the not-allowed screen with **Sign out**, and no app content
- [ ] Signing out clears the flag and shows the sign-in screen
- [ ] The screen works with the keyboard, at phone width and in both themes
- [ ] A `401` still ends the session as in FE-015
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Temporarily remove your user ID from `CLERK_ALLOWED_USER_IDS` in `api/.env`, restart the API, reload the app: the not-allowed screen shows. Restore the value afterwards.
2. Click **Sign out**: back to the sign-in screen; sign in again after restoring the ID: the app shows.

## Review guide

Read the diff in this order, and check:

1. `authView.ts`: priority order and the new input.
2. `NotAllowedScreen.tsx`: states and wording.
3. Does anything keep calling the API while the screen shows?

Things that should *not* be in the diff: Account switching, support links, any change to the API.

## Out of scope

- Per-user data → a later epic; the app stays single-owner.

## Notes / log

The agent adds progress notes, decisions and open questions here.
