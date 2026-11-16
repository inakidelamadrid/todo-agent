# FE-012: The request helper adds `Authorization: Bearer` from an injected token getter

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design (Web app), §5.2 Session handling
- **Assigned agent / harness / model:**
- **Depends on:** FE-002
- **Can run in parallel with:** BE-058 to BE-064, FE-009 to FE-011
- **Review size:** ~50 lines, 2 files plus tests, ~10 min

## Goal

`createRequest` in `web/src/lib/api.ts` takes an optional `getToken` and sends `Authorization: Bearer <token>` on every request when it returns one. It knows nothing about Clerk.

## Why this ticket exists

The helper stays pure and testable by taking the token source as an argument. FE-013 supplies Clerk's real getter. Building on FE-002 (the extracted helper) means this is a small change to one function.

## Read first

- `web/src/lib/api.ts` (created by FE-002) and `web/src/features/bills/api/client.test.ts`: how a fake `fetch` is injected.
- `web/src/lib/api.test.ts`.

## Design

- **Pattern:** Higher-order function with dependency injection: the token source is a parameter, as `fetch` already is.
- **Data flow:** `createRequest(fetch, '/api', getToken)` → each call awaits `getToken()` → adds the header → `fetch`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/lib/api.ts` (changed): `createRequest(fetchImpl, base, getToken?: () => Promise<string | null>)`. On every call, `await getToken()` (a fresh token each time; Clerk caches and refreshes it). A non-null token adds `Authorization: Bearer <token>`. If `getToken` is absent, returns `null`, or rejects, no header is sent and the request still goes out; the server's `401` then drives FE-015. The token is never logged and never put in an error message.
- `web/src/lib/api.test.ts` (changed).

No other file changes. Existing callers keep working because the parameter is optional.

## Steps

1. Add the parameter and the header logic.
2. Write the tests, red first.
3. Run `make web-test` and `make web-build`.

## Tests

- `test_adds_bearer_header_when_token_is_returned`.
- `test_no_header_when_token_is_null`.
- `test_no_header_and_request_still_sent_when_getter_rejects`.
- `test_asks_for_a_fresh_token_on_every_request`: two requests → two getter calls.
- `test_token_never_appears_in_thrown_api_error`: a `401` response error message does not contain the token.
- `test_existing_calls_unchanged_without_getter`.

## Acceptance criteria

- [ ] `createRequest` accepts an optional `getToken` and sends the bearer header when it yields a token
- [ ] A missing, null or failing getter sends no header and does not throw
- [ ] A token is requested per call, never stored in the module
- [ ] The token never appears in an error message
- [ ] Existing tests pass untouched
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-test`: green.
2. `grep -n "Authorization" web/src -r`: only `api.ts` and its test.

## Review guide

Read the diff in this order, and check:

1. `web/src/lib/api.ts`: is the token read per call, and is there no module-level state?
2. Are the failure paths (null, rejection) covered?

Things that should *not* be in the diff: Anything importing `@clerk/react`, wiring into the bills client, handling of `401`.

## Out of scope

- Supplying Clerk's getter → FE-013.
- Reacting to `401` → FE-015.

## Notes / log

The agent adds progress notes, decisions and open questions here.
