# BE-064: `GET /me` and the `require_user` dependency

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.5 `GET /me`, §5.3
- **Assigned agent / harness / model:**
- **Depends on:** BE-063
- **Can run in parallel with:** FE-009 to FE-016
- **Public endpoint?** no
- **Review size:** ~40 lines, 4 files plus tests, ~8 min

## Goal

`GET /me` returns `{"userId": "…", "kind": "user"}` for a signed-in owner and `403` for a machine, and `require_user` is available for any later route a machine must not call.

## Why this ticket exists

Later epics need 'a person, not a script' (EPIC-006 reveal, BE-046 pairing). This adds that dependency and proves it with the smallest possible route, which also gives the web app a way to ask whether the API accepts its session.

## Read first

- `api/app/routes/public.py`: the smallest router in the app.
- `api/app/bills/schemas.py`: `_CamelModel`, the camelCase config to copy (aliases, populate by name).
- `api/app/security.py` (BE-062).

## Design

- **Pattern:** Dependency composition: `require_user` builds on `require_principal`, so there is still one place that reads credentials.
- **Data flow:** request → `require_principal` → `require_user` (`User` or `403`) → route → `MeResponse`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/security.py` (changed): `require_user(principal = Depends(require_principal)) -> User`; a `Machine` raises `HTTPException(403, "A signed-in user is required")`.
- `api/app/routes/me.py` (new): `router = APIRouter()`, `GET /me`, response model `MeResponse(user_id: str, kind: Literal["user"])` with the same camelCase config as `_CamelModel`. Do not import the private `_CamelModel`; copy its three-line config, or promote it to a shared module only if the ticket stays within size.
- `api/app/main.py` (changed): `app.include_router(me.router, dependencies=[Depends(require_user)])`.

**API**

| Case | Status | Body |
|---|---|---|
| Owner session token | `200` | `{"userId": "user_owner", "kind": "user"}` |
| Valid API key | `403` | `{"detail": "A signed-in user is required"}` |
| No credentials / bad token | `401` | as BE-062 |
| Token of a non-owner | `403` | `{"detail": "Not allowed"}` |

## Steps

1. Add `require_user` and its test.
2. Add the route and the model.
3. Mount it and run the whole suite.

## Tests

- `test_me_returns_user_for_owner_token`: camelCase body.
- `test_me_with_api_key_returns_403`.
- `test_me_without_credentials_returns_401`; `test_me_with_wrong_api_key_returns_401`.
- `test_me_with_non_owner_token_returns_403`.
- `test_require_user_returns_the_user_object`.

## Acceptance criteria

- [ ] `GET /me` returns `{"userId", "kind": "user"}` in camelCase for the owner
- [ ] A machine with a valid key gets `403`; missing or wrong credentials get `401`
- [ ] `require_user` exists and is the only 'person required' check
- [ ] The route is mounted behind a dependency, not public
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. With the API running: `curl -i -H "X-API-Key: <key>" http://127.0.0.1:8000/me` → `403`.
3. After FE-013, from the signed-in app's browser console: `await (await fetch('/api/me', {headers: {Authorization: 'Bearer ' + await window.Clerk.session.getToken()}})).json()` → `{userId: 'user_…', kind: 'user'}`.

## Review guide

Read the diff in this order, and check:

1. `api/app/security.py`: does `require_user` read nothing itself?
2. `api/app/routes/me.py`: is the JSON camelCase and the model frozen or read-only?
3. `api/app/main.py`: is the route behind `require_user`?

Things that should *not* be in the diff: User profile data, database access, Clerk SDK calls.

## Out of scope

- Unblocking BE-046 (Telegram pairing) → it now depends on this ticket.
- Step-up re-auth → deferred to EPIC-006.

## Notes / log

The agent adds progress notes, decisions and open questions here.
