# FE-017: Remove the API key from the Vite dev proxy

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design (Web app), §7 Security, §8 acceptance criteria
- **Assigned agent / harness / model:**
- **Depends on:** FE-013
- **Can run in parallel with:** none
- **Review size:** ~30 lines, 4 files plus tests, ~8 min

## Goal

The dev proxy only forwards `/api/*`; it no longer adds `X-API-Key`, and the browser authenticates with its Clerk token alone. `API_KEY` is gone from `web/.env.example` and the docs.

## Why this ticket exists

This closes the epic's main promise: the browser never holds or triggers an API key. It comes last so the app keeps working at every step before it.

## Read first

- `web/vite.config.ts`: `apiProxy`, its `API_KEY` check and the placeholder warning.
- `web/.env.example`.
- Anywhere the docs mention `API_KEY` for the web app: `grep -rn "API_KEY" README.md web Makefile CLAUDE.md --include=*.md --include=Makefile` (CLAUDE.md is owner-edited: report, do not edit).

## Design

- **Pattern:** Removal, with the function exported so it can be tested.
- **Data flow:** browser `/api/*` → proxy (path rewrite only) → API.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/vite.config.ts` (changed): `apiProxy(env)` no longer reads `API_KEY`, no longer throws when it is missing, no longer warns about the placeholder, and sets no `headers`. It keeps `target` (from `API_URL`), `changeOrigin` and the `/api` rewrite. Export `apiProxy` for the test.
- `web/.env.example` (changed): drop the `API_KEY` lines and their comment; keep `API_URL`; keep `VITE_CLERK_PUBLISHABLE_KEY`.
- Docs that mention `API_KEY` for the web app (changed, if any): remove or correct them.
- `web/src/lib/viteProxy.test.ts` (new): imports `apiProxy` and checks it.

**Human step:** delete `API_KEY` from your `web/.env.local` (harmless if left; it is simply unused).

## Steps

1. Simplify `apiProxy` and export it.
2. Write the test.
3. Update `.env.example` and docs.
4. Build and grep the bundle.

## Tests

- `test_proxy_sets_no_api_key_header`: the returned `/api` entry has no `headers`.
- `test_proxy_does_not_need_api_key`: calling it with an empty env does not throw.
- `test_proxy_rewrites_the_api_prefix_and_targets_api_url`.

## Acceptance criteria

- [ ] `vite.config.ts` has no reference to `API_KEY` and adds no `X-API-Key`
- [ ] The bills screen works signed in without `API_KEY` set
- [ ] A signed-out browser calling `/api/bills` gets `401`
- [ ] `grep -ri "x-api-key\|API_KEY" web/dist` finds nothing after a build
- [ ] `web/.env.example` and the docs no longer mention `API_KEY` for the web app
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Remove `API_KEY` from `web/.env.local`, `make web-dev`, sign in: the bills screen works.
2. Open the app signed out in a private window and in the console run `await fetch('/api/bills').then(r => r.status)` → `401`.
3. `make web-build && grep -ri "x-api-key\|API_KEY" web/dist; echo $?` → prints nothing, then `1`.

## Review guide

Read the diff in this order, and check:

1. `vite.config.ts`: is it simpler, with no leftover branches?
2. Did any doc still tell people to set `API_KEY`?

Things that should *not* be in the diff: CORS, production hosting, deleting `API_KEYS` from the API (machines still use it).

## Out of scope

- Calling the API from a production build (hosting is undecided) → the hosting epic.
- Step-up re-auth → EPIC-006.

## Notes / log

The agent adds progress notes, decisions and open questions here.
