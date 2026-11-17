# FE-013: Send Clerk's session token with every API call

- **Status:** done
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design (Web app), §5.2
- **Assigned agent / harness / model:** Platform / Antigravity / Gemini 4 Argon (Medium)
- **Depends on:** FE-010, FE-012, BE-063
- **Can run in parallel with:** FE-014
- **Review size:** ~35 lines, 3 files plus tests, ~10 min

## Goal

The bills client calls the API with a fresh Clerk session token, and the API accepts it. A signed-in browser proves it by asking `/api/me`.

## Why this ticket exists

The first end-to-end check that the whole chain works: Clerk issues, the browser sends, the API verifies. It is a one-line wiring on top of FE-012, kept apart so this check, and the real-token claim question left open in BE-061, has a ticket of its own.

## Read first

- `web/src/lib/api.ts` (FE-012) and where the bills client builds its request (`web/src/features/bills/api/client.ts` and the store that creates it).
- Clerk docs (https://clerk.com/docs/references/react/overview): how to read the session token outside a React hook (`window.Clerk.session.getToken()` or the SDK's equivalent). Check the exact API for the installed version.

## Design

- **Pattern:** Adapter at the edge: one small function that adapts Clerk's global to the `() => Promise<string | null>` shape.
- **Data flow:** `getSessionToken()` → `createRequest(fetch, '/api', getSessionToken)` → `Authorization: Bearer …` → API.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/lib/sessionToken.ts` (new): `getSessionToken(): Promise<string | null>` returns the current session's token, or `null` when there is no session or Clerk has not loaded. It does not cache the token.
- `web/src/features/bills/api/client.ts` and the place that creates the shared request (changed): pass `getSessionToken` as the third argument.
- `web/src/lib/sessionToken.test.ts` (new): with a stubbed global.

The dev proxy still adds `X-API-Key`. That is fine: the bearer token wins in BE-062, so this ticket tests the real path. FE-017 removes the proxy key afterwards.

## Steps

1. Write `getSessionToken` with a stubbed-global test.
2. Pass it where the request is created.
3. Run the tests, then check by hand.

## Tests

- `test_returns_the_token_from_the_current_session`.
- `test_returns_null_without_a_clerk_global`.
- `test_returns_null_without_a_session`.
- `test_does_not_cache_between_calls`.

## Acceptance criteria

- [x] Every `/api/*` call from the app carries `Authorization: Bearer …`
- [ ] The bills screen works signed in
- [ ] `GET /api/me` with the session token returns `{"userId": …, "kind": "user"}` (needs BE-064; until then `/api/bills` is the check)
- [ ] A real Clerk token passes the API's checks, including `azp` (confirms the BE-061 assumption)
- [x] The token is not printed anywhere
- [x] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-dev` and `make web-dev`, sign in. The bills list loads.
2. In the browser dev tools network panel, open one `/api/bills` request: the request headers include `Authorization: Bearer …`. Do not copy the value anywhere.
3. In the console: `await (await fetch('/api/me', {headers: {Authorization: 'Bearer ' + await window.Clerk.session.getToken()}})).json()` → your user ID. If it returns `401`, a claim differs from what BE-059 expects: write which one in the Notes.

## Review guide

Read the diff in this order, and check:

1. `web/src/lib/sessionToken.ts`: no caching, no logging?
2. Where the request is created: is the getter the only change?

Things that should *not* be in the diff: Removing the proxy key (FE-017), handling `401` (FE-015), any Clerk secret.

## Out of scope

- Handling `401` and `403` → FE-015, FE-016.
- Removing the proxy key → FE-017.

## Assumptions

- The real Clerk session token carries `azp`. If it does not, BE-059's rule changes in a follow-up before this ticket is accepted.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/FE-013`.
- Added `getSessionToken` in `web/src/lib/sessionToken.ts` reading `(globalThis as ClerkGlobal).Clerk?.session?.getToken()` without caching or logging (`globalThis.Clerk` is what `@clerk/react` 6.18.8 sets in the browser, equivalent to `window.Clerk`, and works in the Node Vitest environment via `vi.stubGlobal`).
- Passed `getSessionToken` as the third argument to `createRequest` in `web/src/features/bills/api/client.ts`.
- `make web-test` → 62 passed (4 new in `sessionToken.test.ts`); `make web-build` passes.
- Manual signed-in browser checks (`GET /api/bills` and `GET /api/me` with a real Google session token) left unchecked for human verification.
