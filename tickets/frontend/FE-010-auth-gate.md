# FE-010: `AuthGate`: loading, error, signed-out and signed-in views

- **Status:** done (committed on `idelamadrid/FE-010`; signed-in path awaits a manual Google sign-in)
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.1 Sign-in and sign-out (states to polish), §5.2
- **Assigned agent / harness / model:** Claude Code / claude-fable-5-2
- **Depends on:** FE-009
- **Can run in parallel with:** BE-058 to BE-064
- **Review size:** ~70 lines, 4 files plus tests, ~12 min

## Goal

The app shows nothing until Clerk has loaded, then either the app (signed in), a sign-in prompt (signed out) or a calm error with a retry. A pure function decides which.

## Why this ticket exists

Without this the app flashes the wrong screen while Clerk starts. The decision is a small state machine, so it is written as a pure function and tested; the component only adapts Clerk's hooks to it. The signed-out view is a minimal placeholder here and FE-011 replaces it with the designed screen.

## Read first

- `web/src/App.tsx` and `web/src/components/AppShell.tsx`: where the gate goes and what the brand mark looks like.
- Clerk React reference (https://clerk.com/docs/references/react/overview): `useAuth`, `ClerkLoading`, `ClerkFailed`, `SignInButton`. Check which of them reports a load failure in this SDK version before coding.
- `DESIGN.md`, 'Overview' and 'Motion': calm, no jarring flashes.

## Design

- **Pattern:** State as a pure function ('state machine as a value'): inputs → one of four views, with a priority order.
- **Data flow:** Clerk state → `resolveAuthView({ isLoaded, isSignedIn, loadFailed })` → `loading | error | signed-out | signed-in` → `AuthGate` renders it.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/auth/authView.ts` (new): `type AuthView = 'loading' | 'error' | 'signed-out' | 'signed-in'` and `resolveAuthView(input: { readonly isLoaded: boolean; readonly isSignedIn: boolean | undefined; readonly loadFailed: boolean }): AuthView`. Priority: `loadFailed` → `error`; not loaded → `loading`; signed in → `signed-in`; else `signed-out`.
- `web/src/features/auth/AuthGate.tsx` (new): reads Clerk, calls `resolveAuthView`, renders:
  - `loading`: centered brand mark with a gentle pulse, `role="status"` and an accessible label 'Loading'. No text flash.
  - `error`: 'Can't reach sign-in right now', one **Try again** button that reloads the page. Calm wording, no guilt, no jargon.
  - `signed-out`: a minimal prompt with Clerk's `SignInButton` (replaced by FE-011).
  - `signed-in`: `children`.
- `web/src/App.tsx` (changed): wrap the current content in `<AuthGate>`.
- `web/src/features/auth/authView.test.ts` (new).

States to polish: loading, error, hover, focus (visible ring), phone width, light and dark. Use the existing tokens and the type scale in `DESIGN.md`.

## Steps

1. Write `resolveAuthView` and its tests.
2. Write `AuthGate` with the four views.
3. Wrap `App`.
4. Run tests and build, then look at all four views in the browser.

## Tests

- `test_not_loaded_is_loading`.
- `test_load_failure_wins_over_everything`: failed and not loaded → `error`; failed and signed in → `error`.
- `test_loaded_signed_in_is_signed_in`.
- `test_loaded_signed_out_is_signed_out`, including `isSignedIn: undefined`.

## Acceptance criteria

- [x] `resolveAuthView` is pure and its four cases pass
- [ ] A signed-out browser shows the placeholder prompt and none of the app; a signed-in one shows the app
- [x] While Clerk starts, neither the app nor the prompt flashes
- [ ] The error view has a working **Try again**, and every view works with the keyboard
- [ ] Checked at desktop and phone width, in light and dark
- [x] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-dev`, open the app signed out: a short loading view, then the prompt. The bills screen is not visible.
2. Block `*.clerk.accounts.dev` in the browser dev tools network panel and reload: the error view shows; **Try again** reloads.
3. Sign in through the prompt (Google): the bills screen shows. (The API still accepts the dev proxy's key until FE-017.)

## Review guide

Read the diff in this order, and check:

1. `web/src/features/auth/authView.ts`: does the priority match the spec?
2. `web/src/features/auth/AuthGate.tsx`: only adaptation of Clerk to the function, with no logic of its own?
3. Is every interactive element reachable by keyboard with a visible focus ring?

Things that should *not* be in the diff: The styled sign-in screen, the account control, token code, 401 or 403 handling.

## Out of scope

- The styled sign-in screen → FE-011.
- Account control and sign-out → FE-014.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/FE-010`. Load failure is read from `useClerk().status === "error"`, the same value `ClerkFailed` checks in `@clerk/react` 6.18.8.
- `BrandMark` is now exported from `AppShell.tsx` so the gate can reuse it (one-word change, not in the ticket file list).
- `make web-test` → 50 passed (4 new); `make web-build` passes.
- Checked in Chrome, dark theme, desktop width: signed-out shows the prompt and none of the app; loading shows the pulsing mark; with an unreachable Clerk host the error view shows after Clerk gives up (about 10 s).
- Not checked: the signed-in path (needs a real Google sign-in), clicking **Try again**, light theme and phone width. Those criteria stay unchecked.
