# BE-063: Switch the routers to `require_principal`; refuse to start without Clerk settings

- **Status:** done (implemented and verified on branch `idelamadrid/BE-063-require-principal-routers`; not committed — awaiting user approval)
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.3, §5.4 Owner allowlist, §7 Security
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** BE-061, BE-062
- **Can run in parallel with:** FE-009 to FE-011
- **Public endpoint?** no
- **Review size:** ~40 lines, 4 files plus tests, ~12 min

## Goal

Every protected router in `main.py` uses `require_principal`, the OpenAPI docs show both schemes, and the app refuses to start unless all three Clerk values are set. API-key callers (the web dev proxy, n8n, scripts) keep working.

## Why this ticket exists

BE-062 built the dependency; this ticket turns it on. It is a refactor in behaviour terms for machines (they are still accepted) and a new rule for configuration (no Clerk values, no start), so the human step of filling `api/.env` happens here.

## Read first

- `api/app/main.py`: `create_app`, the router wiring and the custom OpenAPI function.
- `api/tests/conftest.py`: `make_client`, the probe router and how `API_KEYS` gets its session default.
- `api/tests/test_auth.py`: the assertions that mention `'Invalid or missing API key'` and `WWW-Authenticate: ApiKey` change here.

## Design

- **Pattern:** Refactor behind a stable seam: the dependency is swapped in one place, the routers do not change.
- **Data flow:** `create_app` → `get_settings` → `clerk_enabled` (else raise) → routers mounted with `Depends(require_principal)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/main.py` (changed):
  - `bills_router` and `payments_router` now mount with `dependencies=[Depends(require_principal)]`. `public.router` (`/health`, `/ping`) stays public, as before (epic open question 7).
  - `create_app` raises `RuntimeError("CLERK_JWT_PUBLIC_KEY, CLERK_AUTHORIZED_PARTIES and CLERK_ALLOWED_USER_IDS must all be set")` when `clerk_enabled(settings)` is false. The message names the variables and never a value.
  - The OpenAPI helper adds a `BearerAuth` scheme (`{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}`) next to `APIKeyHeader`.
- `api/tests/conftest.py` (changed): before the app is imported, generate an RSA key pair, set `CLERK_JWT_PUBLIC_KEY` (the public PEM), `CLERK_AUTHORIZED_PARTIES=http://localhost:5173` and `CLERK_ALLOWED_USER_IDS=user_owner` with `os.environ.setdefault`; the probe router uses `require_principal`; add a `fake_decoder` override for tests that need a signed-in user.
- `api/tests/test_auth.py` (changed): expected `detail` becomes `"Invalid or missing credentials"` and the header `"Bearer, ApiKey"`; add the start-up and token cases below.
- `api/tests/test_bills_api.py` and others: should pass unchanged (API key → `Machine`). If one needs a change, say why in Notes.

**Human step:** fill the three values in your real `api/.env` (see BE-058) before running the API again, or it will not start. This is intended.

## Steps

1. Update `conftest.py` so the suite has Clerk settings.
2. Swap the dependency in `main.py` and add the start-up check and the OpenAPI scheme.
3. Update and add the tests.
4. Run `make api-test`, then start the API by hand.

## Tests

- `test_app_refuses_to_start_without_clerk_values`: each of the three missing → `RuntimeError`, message has no value.
- `test_protected_route_with_valid_api_key_still_works` (machine).
- `test_protected_route_with_owner_token_works`: fake decoder, valid claims → `200`.
- `test_protected_route_with_other_user_token_returns_403`.
- `test_protected_route_with_expired_token_returns_401`.
- `test_public_routes_stay_public`: `/health` and `/ping` need no credential.
- `test_openapi_lists_both_security_schemes`.
- Bills and payments tests keep passing unchanged.

## Acceptance criteria

- [x] `bills_router` and `payments_router` use `require_principal`; `/health` and `/ping` stay public
- [x] The app does not start unless all three Clerk values are set, and the error never shows a value
- [x] A valid `X-API-Key` still gets through every protected route
- [x] `/openapi.json` lists the bearer and API-key schemes
- [x] The existing bills tests pass without edits to their assertions
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. With the three Clerk values set in `api/.env`: `make api-dev`, then `curl -i http://127.0.0.1:8000/bills` → `401`; with `-H "X-API-Key: <your key>"` → `200`.
3. Blank one Clerk value and start again: the app exits with the message naming the variables.

## Review guide

Read the diff in this order, and check:

1. `api/app/main.py`: are both routers swapped, and is nothing else public?
2. `api/tests/conftest.py`: is the key pair generated in the test run, with no real value committed?
3. `api/tests/test_auth.py`: do the new assertions still cover missing and wrong credentials?

Things that should *not* be in the diff: New routes, changes to `bills/`, the web app, `require_api_key` deleted (it may stay unused; removing it is not needed here).

## Out of scope

- `GET /me` → BE-064.
- Removing the key from the web dev proxy → FE-017.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-063-require-principal-routers`. `main.py` swaps both business routers to `require_principal`, refuses to start without all three Clerk values (message names the variables, never a value), and adds `BearerAuth` to the OpenAPI schemes next to `APIKeyHeader`. Public routes untouched; `require_api_key` remains (unused) for later removal.
- **Deviation from the ticket (better):** instead of a fake-decoder override for signed-in tests, the suite signs REAL RS256 tokens and runs them through the real BE-061 decoder end to end. `tests/keys.py` holds a **static test-only key pair** as constants — documented as intentionally-committed non-credentials.
  - Root cause discovered while debugging: a *generated* key pair breaks under `pytest -n auto` because the xdist controller imports conftest (generating pair A, inherited by worker env at spawn) while each worker's test module generates pair B → signature verification failed only in parallel runs. The static pair makes every process agree. Logged for the reviewer because it's the kind of failure that looks like flakiness.
- `test_auth.py` rewritten for the dual scheme (new detail text + both challenges); old behaviors kept (wrong key, echo-free responses, API_KEYS validators).
- `test_settings_clerk.py` gained an autouse env-isolation fixture because conftest now sets CLERK_* process env defaults.
- Bills/payments integration tests pass unchanged with API keys (Machine path), per the acceptance criterion.
- `make api-test` → 180 passed, **5 consecutive parallel runs** (the key-pair bug was the flaky one).
- ⚠️ For the human's hand check: `python-dotenv` warns "could not parse statement starting at line 21" while reading `api/.env` — the pasted `CLERK_JWT_PUBLIC_KEY` likely has real newlines.
- **User-requested tooling added (extra scope, mid-ticket):** `api/scripts/clerk_jwks.py` with `make clerk-key-check` (validates dotenv-parseability AND RSA key structure, message only) and `make clerk-key-fix` (prints a paste-ready one-line assignment; **never edits `.env`**). The real key was confirmed broken exactly as predicted (real-newline paste) and `clerk-key-fix` already produced the corrected line. Runbook step 4 references both. 8 new tests; 188 passed total.
