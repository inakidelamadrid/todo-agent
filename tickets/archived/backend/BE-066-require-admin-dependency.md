# BE-066: `require_admin`: the shared admin-only dependency

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-065
- **Can run in parallel with:** BE-067, BE-069
- **Public endpoint?** no
- **Review size:** ~30 lines, 1 file plus tests, ~8 min

## Goal

`require_admin` in `api/app/security.py` returns the `User` when they are an admin and raises `403` for any other signed-in user or machine.

## Why this ticket exists

Every playground endpoint must be admin-only through one shared dependency, the same way `require_user` is the one 'person required' check. It composes `require_principal`, so credentials are still read in exactly one place.

## Read first

- `api/app/security.py`: `require_user` (BE-064) is the shape to copy.
- `api/tests/test_principal_dependency.py`: the throwaway-app test style.

## Design

- **Pattern:** Dependency composition: `require_principal` → `require_admin`. No header is read here.
- **Data flow:** request → `require_principal` → `is_admin(principal, parse_csv(settings.admin_user_ids))` → `User` or `403`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/security.py` (changed).

```python
DETAIL_ADMIN_REQUIRED = "Admin access is required"

def require_admin(
    principal: Annotated[Principal, Depends(require_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User: ...
```

- Admin `User` → returned.
- Any other `User`, or a `Machine` → `HTTPException(403, DETAIL_ADMIN_REQUIRED)`.
- Missing or bad credentials never reach this function: `require_principal` already answered `401`.

`api/tests/test_require_admin.py` (new): a throwaway `FastAPI()` with one route, the fake decoder and overridden settings.

## Steps

1. Write the tests with a throwaway app.
2. Add the dependency.
3. Run `make api-test`.

## Tests

- `test_admin_user_passes_and_gets_user_object`.
- `test_non_admin_user_gets_403`.
- `test_machine_gets_403`.
- `test_no_credentials_gets_401`; `test_wrong_api_key_gets_401`.
- `test_empty_admin_list_denies_everyone`.

## Acceptance criteria

- [ ] `require_admin` returns the admin `User` and raises `403` for non-admins and machines
- [ ] Missing or wrong credentials still give `401` with `WWW-Authenticate`
- [ ] The function reads no header itself
- [ ] No router uses it yet
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_require_admin.py -q`: green.
2. `make api-test`: nothing else changed.

## Review guide

Read the diff in this order, and check:

1. `require_admin`: is it only composition plus `is_admin`?
2. Tests: are both `401` cases and both `403` cases present?

Things that should *not* be in the diff: Routes, the playground switch, role data on `/me`.

## Out of scope

- `roles` on `GET /me` → BE-067.
- The playground router → BE-068.

## Notes / log

The agent adds progress notes, decisions and open questions here.
