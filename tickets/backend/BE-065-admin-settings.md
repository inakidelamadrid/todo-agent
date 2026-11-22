# BE-065: Admin settings: `ADMIN_USER_IDS` and the pure `is_admin`

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-069, FE-019
- **Public endpoint?** no
- **Review size:** ~30 lines, 3 files plus tests, ~6 min

## Goal

`Settings` holds `admin_user_ids`, and `is_admin(user, admin_ids)` in `api/app/principal.py` says whether a principal is an admin. Nothing uses it yet.

## Why this ticket exists

The playground is admin-only, and 'admin' does not exist in the code yet. This adds the smallest possible definition: a list of Clerk user IDs from the environment and one pure function. More admins are expected later (epic question 9), so it is a list from the start.

## Read first

- `api/app/settings.py`: `parse_csv` and the `clerk_allowed_user_ids` field (same shape).
- `api/app/principal.py`: `User`, `Machine`, `Principal`.
- `api/.env.example`: the Clerk block.

## Design

- **Pattern:** Plain pure function. Fail closed: an empty list means nobody is an admin.
- **Data flow:** `ADMIN_USER_IDS` → `Settings.admin_user_ids` → `parse_csv` → `is_admin(principal, ids)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/settings.py` (changed): `admin_user_ids: str = ""`. Optional: an empty value does **not** stop the app from starting; it only means no admin exists.
- `api/app/principal.py` (changed): `def is_admin(principal: Principal, admin_user_ids: tuple[str, ...]) -> bool` (pure). True only for a `User` whose `user_id` is in the tuple. A `Machine` is never an admin, whatever the list holds.
- `api/.env.example` (changed):

```
# Clerk user IDs with admin rights (debugger playground), comma-separated.
# Admins must also be in CLERK_ALLOWED_USER_IDS to sign in at all.
ADMIN_USER_IDS=
```

- `api/tests/test_admin.py` (new).

**Human step:** put your own Clerk user ID in `ADMIN_USER_IDS` in `api/.env`. The value is never written in the repository.

## Steps

1. Add the setting and the function.
2. Write the tests.
3. Document the variable.
4. Run `make api-test`.

## Tests

- `test_user_in_list_is_admin`.
- `test_user_not_in_list_is_not_admin`.
- `test_machine_is_never_admin`: even when its `key_label` equals a listed ID.
- `test_empty_list_means_no_admins`.
- `test_app_starts_without_admin_user_ids`.

## Acceptance criteria

- [ ] `Settings.admin_user_ids` exists, defaults to empty, and the app starts without it
- [ ] `is_admin` is pure and true only for a listed `User`
- [ ] A `Machine` is never an admin
- [ ] `api/.env.example` documents the variable with no real value
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_admin.py -q`: green.
2. `grep -n ADMIN_USER_IDS api/.env.example`: present and empty.

## Review guide

Read the diff in this order, and check:

1. `api/app/principal.py`: does `is_admin` check the type before the list?
2. `api/app/settings.py`: is the field optional?

Things that should *not* be in the diff: A dependency, a route, any role stored in the database.

## Out of scope

- The `require_admin` dependency → BE-066.
- An admins table with a screen → not planned yet (epic question 9).

## Notes / log

The agent adds progress notes, decisions and open questions here.
