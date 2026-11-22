# BE-067: `GET /me` returns `roles`

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-065
- **Can run in parallel with:** BE-066, BE-069
- **Public endpoint?** no
- **Review size:** ~25 lines, 1 file plus tests, ~6 min

## Goal

`GET /me` answers `{"userId": "…", "kind": "user", "roles": ["admin"]}` for an admin and `"roles": []` for anyone else.

## Why this ticket exists

The web app needs to know whether to show the playground entry. Hiding it is a courtesy; the API check (BE-066) is the one that counts. Paired with FE-018.

## Read first

- `api/app/routes/me.py`: the whole file.
- `api/tests/` tests for `/me` (BE-064).

## Design

- **Pattern:** Plain route change; the role list is derived by the pure `is_admin`.
- **Data flow:** `require_user` → route → `is_admin` → `MeResponse(roles=...)`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/routes/me.py` (changed).

- `MeResponse` gains `roles: tuple[Literal["admin"], ...] = ()`.
- The route takes `settings: Annotated[Settings, Depends(get_settings)]` and sets `roles=("admin",)` when `is_admin(principal, parse_csv(settings.admin_user_ids))`.

| Case | Body |
|---|---|
| Admin | `{"userId": "user_owner", "kind": "user", "roles": ["admin"]}` |
| Signed-in non-admin | `{"userId": "user_x", "kind": "user", "roles": []}` |

Status codes are unchanged from BE-064 (`401`, `403` for a machine).

## Steps

1. Extend the model and the route.
2. Add the tests.
3. Run `make api-test`.

## Tests

- `test_me_roles_is_admin_for_listed_user`.
- `test_me_roles_is_empty_for_other_user`.
- `test_me_still_rejects_machine_with_403`.
- `test_me_without_credentials_returns_401`; `test_me_with_wrong_api_key_returns_401` (existing, still green).

## Acceptance criteria

- [ ] `roles` is `["admin"]` for an admin and `[]` otherwise, in camelCase JSON
- [ ] Existing `/me` behaviour and tests are unchanged
- [ ] No user ID from the admin list leaks to a non-admin
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. Signed in as the admin, in the browser console: `await (await fetch('/api/me', {headers: {Authorization: 'Bearer ' + await window.Clerk.session.getToken()}})).json()` → includes `roles: ['admin']`.

## Review guide

Read the diff in this order, and check:

1. `me.py`: is the role derived only through `is_admin`?

Things that should *not* be in the diff: Other roles, profile data.

## Out of scope

- Using `roles` in the web app → FE-018.

## Notes / log

The agent adds progress notes, decisions and open questions here.
