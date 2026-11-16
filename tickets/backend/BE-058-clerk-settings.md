# BE-058: Clerk settings: three env vars and their parsers

- **Status:** done (implemented and verified on branch `idelamadrid/BE-058-clerk-settings`; not committed — awaiting user approval)
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.4 Owner allowlist, §5.7 Configuration and secrets
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** none
- **Can run in parallel with:** FE-009, BE-059
- **Public endpoint?** no
- **Review size:** ~40 lines, 3 files, ~8 min

## Goal

`Settings` holds the three Clerk values (`clerk_jwt_public_key`, `clerk_authorized_parties`, `clerk_allowed_user_ids`), with pure parsers and a `clerk_enabled` check, and `api/.env.example` documents them. Nothing uses them yet.

## Why this ticket exists

Every later backend ticket reads these values. Adding them alone, optional and unused, leaves `main` green: the app keeps starting with only `API_KEYS`. BE-063 is the ticket that makes them mandatory at start-up, once the dependency actually uses them.

## Read first

- `api/app/settings.py`: `parse_api_keys` and `telegram_enabled` are the shapes to imitate (a pure parser, and a fail-closed `*_enabled`).
- `api/.env.example`: how existing settings are documented.
- Clerk docs, 'Manual JWT verification': https://clerk.com/docs/backend-requests/manual-jwt (where the public key and the `azp` claim are explained).

## Design

- **Pattern:** Plain functions, no pattern. Same fail-closed idea as `telegram_enabled`: unset means denied.
- **Data flow:** environment → `Settings` (frozen) → `parse_csv` / `normalize_pem` → used by BE-062.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/settings.py` (changed):
  - Three fields on `Settings`, all defaulting to `""`: `clerk_jwt_public_key: str`, `clerk_authorized_parties: str`, `clerk_allowed_user_ids: str`.
  - `parse_csv(raw: str) -> tuple[str, ...]` (pure): split on commas, strip, drop empties. `parse_api_keys` stays as it is; do not rewrite it.
  - `normalize_pem(raw: str) -> str` (pure): replaces the two characters `\n` with a real newline and strips surrounding whitespace, because a multi-line PEM is easier to keep on one line in a `.env` file.
  - `clerk_enabled(settings: Settings) -> bool` (pure): true only when all three values are non-empty after parsing.
- `api/.env.example` (changed): the three variables, each with a comment (below).
- `api/tests/test_settings_clerk.py` (new).

**`.env.example` additions**

```
# Clerk (user login). The public key is public by design, but keep it out of git anyway.
# Clerk dashboard → API keys → "Show JWT public key" → PEM. Newlines may be written as \n.
CLERK_JWT_PUBLIC_KEY=
# Origins the browser app is served from, comma-separated (the token's `azp` claim).
CLERK_AUTHORIZED_PARTIES=http://localhost:5173
# Clerk user IDs allowed in, comma-separated. Only the owner. Looks like user_2abc…
CLERK_ALLOWED_USER_IDS=
```

**Human step (before BE-062 can be tried by hand, not needed for this ticket's tests)**

Create the Clerk application (development instance): enable Google, set sign-up to **Restricted**, create your user by signing in once (or inviting yourself), copy your user ID, and fill the three values in `api/.env`. Agents never read, print or log these values.

## Steps

1. Add the three fields and the two parsers to `settings.py`; add `clerk_enabled`.
2. Write the tests (below) and see them fail first.
3. Document the variables in `api/.env.example`.
4. Run `make api-test`.

## Tests

- `test_parse_csv_splits_trims_and_drops_empties`: `' a , ,b,'` → `('a', 'b')`; `''` → `()`.
- `test_normalize_pem_turns_escaped_newlines_into_real_ones`: `'-----BEGIN X-----\\nabc\\n-----END X-----'` gains real newlines; an already multi-line value is unchanged apart from trimming.
- `test_clerk_enabled_false_when_any_value_is_missing`: each of the three missing in turn → false.
- `test_clerk_enabled_true_when_all_three_are_set`.
- `test_settings_still_start_without_clerk_values`: `Settings()` with only `API_KEYS` builds (nothing becomes mandatory yet).

## Acceptance criteria

- [x] `Settings` has the three fields, defaulting to empty, and the app still starts with only `API_KEYS` set
- [x] `parse_csv`, `normalize_pem` and `clerk_enabled` are pure functions with the tests above
- [x] `api/.env.example` documents all three variables, with no real value
- [x] A validation error never echoes a Clerk value (the model already sets `hide_input_in_errors`)
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: all green.
2. `grep -n CLERK api/.env.example`: three variables, empty or `http://localhost:5173`.
3. Start the API with your existing `api/.env`: it still starts.

## Review guide

Read the diff in this order, and check:

1. `api/app/settings.py`: is every new function pure, and is `clerk_enabled` fail-closed?
2. `api/.env.example`: does it hold no real value?
3. The tests: is each parser case above covered?

Things that should *not* be in the diff: A validator that refuses to start (BE-063), any JWT code (BE-061), a Clerk package.

## Out of scope

- Refusing to start when the values are empty → BE-063.
- Using the values to check a token → BE-059 and BE-062.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-058-clerk-settings`. Three fields + `parse_csv`, `normalize_pem`, `clerk_enabled` in `settings.py`; vars documented in `api/.env.example`; `parse_api_keys` untouched as instructed.
- Tests use `Settings(_env_file=None)` everywhere (the BE-005 rule) so a developer's real `api/.env` can never leak into output.
- One correction while testing: the ticket's "non-empty after parsing" applies `parse_csv` to the two list fields and `normalize_pem`+trim to the PEM — a separator-only PEM (",") is technically non-empty, so the false-case for it is only tested on CSV fields.
- `make api-test` → 115 passed (6 new).
- **Runbook:** `RUNBOOK-clerk-setup.md` (repo root) walks the human step: create the dev application, Google sign-in, Restricted sign-up, create the user, copy the JWT public key PEM and user ID, fill `api/.env`, validate with a boolean-only one-liner (`clerk_enabled: True`).
