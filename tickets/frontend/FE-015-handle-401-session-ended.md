# FE-015: A `401` from the API ends the session calmly

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.2 Session handling
- **Assigned agent / harness / model:**
- **Depends on:** FE-013
- **Can run in parallel with:** FE-014
- **Review size:** ~50 lines, 4 files plus tests, ~12 min

## Goal

When the API answers `401`, the app signs out of Clerk, shows the sign-in screen and a calm toast 'Your session ended. Please sign in again.'. Several simultaneous `401`s show one toast.

## Why this ticket exists

A `401` means the token was rejected even after Clerk's refresh, so the session is over. Handling it in one place, from the request helper, beats every screen checking for it. The `403` branch of the same hook is added in FE-016.

## Read first

- `web/src/lib/api.ts` (FE-012, FE-013): where an error response becomes `ApiError`.
- `web/src/features/bills/store/`: Zustand state lives at module level, so it survives the gate unmounting the app. Local component state does not.
- `sonner` toast ids: https://sonner.emilkowal.ski/ (a fixed `id` replaces rather than duplicates).

## Design

- **Pattern:** Callback injection plus a pure classifier: `describeAuthFailure(status)` decides what a status means; the handler does the side effect at the edge.
- **Data flow:** response `401` → `createRequest` calls `onAuthFailure(401)` → `handleAuthFailure` → `describeAuthFailure` → `clerk.signOut()` + toast → `AuthGate` shows signed-out.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/lib/api.ts` (changed): optional `onAuthFailure?: (status: 401 | 403) => void`, called when a response is `401` or `403`; the request still throws `ApiError` as before.
- `web/src/features/auth/authFailure.ts` (new): `describeAuthFailure(status: number): 'session-ended' | 'forbidden' | null` (pure) and `handleAuthFailure(status)`: for `session-ended` calls `window.Clerk?.signOut()` and `toast('Your session ended. Please sign in again.', { id: 'session-ended' })`; for `forbidden` does nothing yet (FE-016).
- The place that creates the request (changed): passes `handleAuthFailure`.
- `web/src/features/auth/authFailure.test.ts` (new) and an added case in `web/src/lib/api.test.ts`.

**Behaviour to know:** unsaved text in a component's local state is lost when the gate unmounts the app. Values kept in the Zustand stores survive. Do not widen this ticket to preserve more; note anything important you find in the Notes.

**Loop guard:** the handler signs out once per `401` burst (the fixed toast id and Clerk's own idempotent `signOut`); it never retries the request automatically.

## Steps

1. Add `onAuthFailure` to the helper.
2. Write `describeAuthFailure` and `handleAuthFailure`.
3. Pass the handler where the request is created.
4. Test, then check by hand.

## Tests

- `test_describe_401_is_session_ended`.
- `test_describe_403_is_forbidden`.
- `test_describe_other_statuses_are_null`: `400`, `404`, `500`, `200`.
- `test_request_calls_on_auth_failure_for_401_and_still_throws`.
- `test_request_does_not_call_it_for_500`.

## Acceptance criteria

- [ ] A `401` signs the user out and shows the sign-in screen with one calm toast
- [ ] Parallel `401`s produce one toast
- [ ] Other errors (`422`, `500`, network) behave exactly as before
- [ ] The request still throws `ApiError`, so screens' own error handling is unchanged
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Signed in, stop the API and restart it with a different `CLERK_JWT_PUBLIC_KEY` (any other freshly generated public PEM), then reload the bills screen: the app signs out and shows the toast. Restore the real key afterwards.
2. Sign in again: back to normal.

## Review guide

Read the diff in this order, and check:

1. `web/src/lib/api.ts`: is the callback the only change, and does the error still throw?
2. `authFailure.ts`: is the classifier pure and the handler free of branching logic?

Things that should *not* be in the diff: The `403` screen, retries, token refresh logic of our own.

## Out of scope

- The `403` screen → FE-016.

## Notes / log

The agent adds progress notes, decisions and open questions here.
