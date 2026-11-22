# BE-062: `require_principal`: one dependency for people and machines

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design, §5.3 Principal and dependency, §7
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** BE-058, BE-060
- **Can run in parallel with:** FE-009 to FE-011
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files plus tests, ~12 min

## Goal

`require_principal` in `api/app/security.py` returns a `User` for a valid owner session token, a `Machine` for a valid API key, `401` for missing or bad credentials and `403` for a valid token from someone who is not the owner. No router uses it yet.

## Why this ticket exists

This is the shared dependency the project rule asks for, now accepting two kinds of caller. Cutting it from the router swap (BE-063) lets the reviewer read the decision logic on its own, tested through a throwaway app, before it can lock anyone out.

## Read first

- `api/app/security.py`: `require_api_key` and `_matches_any`; keep both and reuse the constant-time comparison.
- `api/tests/test_auth.py`: the missing-key and wrong-key tests to extend for two credential kinds.
- `api/app/principal.py` and `api/app/session_token.py` (BE-059, BE-060).

## Design

- **Pattern:** A pure resolver wrapped by a thin FastAPI dependency (functional core, imperative shell). Rejections are values mapped to HTTP in exactly one place.
- **Data flow:** headers → `resolve_principal(authorization, api_key, valid_keys, decode, rules, now)` → `User | Machine | Denied(status, detail)` → dependency returns it or raises `HTTPException`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/security.py` (changed), added beside `require_api_key` (which stays, untouched, until BE-063):

```python
@dataclass(frozen=True)
class Denied:
    status: int            # 401 or 403
    detail: str

MACHINE_LABEL = "api-key"   # placeholder until F-2 names keys

def resolve_principal(
    authorization: str | None, api_key: str | None, *,
    valid_keys: tuple[str, ...], decode: DecodeToken, rules: ClerkRules, now: int,
) -> Principal | Denied: ...

def require_principal(...) -> Principal: ...   # FastAPI dependency
```

- `get_now() -> int` (returns `int(time.time())`) as its own dependency so tests can pin the clock.
- `api/tests/test_principal_dependency.py` (new), using a throwaway `FastAPI()` with one route and `dependency_overrides` for the decoder, settings and clock.

**Rules**

1. If `Authorization` starts with `Bearer ` (case-insensitive scheme), the bearer wins: `verify_session`. `User` → return it. Rejection mapping: `not_owner` → `403 "Not allowed"`; `malformed`, `expired`, `not_yet_valid`, `wrong_party` → `401 "Invalid or missing credentials"`. A bad bearer is never rescued by a valid `X-API-Key` sent with it.
2. Otherwise, if `X-API-Key` is present and matches any key (`secrets.compare_digest`) → `Machine(MACHINE_LABEL)`.
3. Otherwise → `401 "Invalid or missing credentials"`. Any other `Authorization` scheme (`Basic`, …) is ignored.
4. Every `401` carries `WWW-Authenticate: Bearer, ApiKey`. Responses never contain the token or the key.
5. The OpenAPI docs must show both schemes: use `HTTPBearer(auto_error=False)` and the existing `APIKeyHeader` as `Security(...)` parameters.
6. `rules` is built from settings with `parse_csv` (BE-058): `ClerkRules(parse_csv(clerk_authorized_parties), parse_csv(clerk_allowed_user_ids))`.

## Steps

1. Write `resolve_principal` and its table of cases first (pure, no FastAPI).
2. Wrap it in `require_principal` and `get_now`.
3. Write the throwaway-app tests.
4. Run `make api-test`.

## Tests

- `test_no_credentials_returns_401_with_both_challenges`.
- `test_wrong_api_key_returns_401`; `test_valid_api_key_returns_machine`.
- `test_valid_owner_token_returns_user`.
- `test_expired_token_returns_401`; `test_token_for_another_origin_returns_401`; `test_malformed_token_returns_401`.
- `test_token_for_non_owner_returns_403`.
- `test_bad_bearer_is_not_rescued_by_valid_api_key`: both sent → `401`.
- `test_valid_bearer_wins_over_wrong_api_key`: both sent, token fine → `User`.
- `test_other_authorization_scheme_is_ignored`: `Basic abc` + valid key → `Machine`.
- `test_responses_never_echo_credentials`: neither the token nor the key appears in any body or header.

## Acceptance criteria

- [x] `require_principal` returns `User` for the owner's token and `Machine` for a valid key
- [x] A missing or wrong credential gives `401` with `WWW-Authenticate`, a non-owner token gives `403`, an expired or other-origin token gives `401`
- [x] `resolve_principal` is pure and unit-tested without FastAPI
- [x] `require_api_key` is unchanged and no router uses `require_principal` yet
- [x] Credentials never appear in a response
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_principal_dependency.py -q`: green.
2. `make api-test`: existing tests unchanged and green.
3. Open `/docs` while running the API: unchanged (the new dependency is not mounted yet).

## Review guide

Read the diff in this order, and check:

1. `api/app/security.py`, `resolve_principal`: read the four rules above against the code, in order.
2. Is the mapping from rejection to status code in one place only?
3. The tests: is there a case for every row of the epic's section 7 list (no credentials, wrong key, expired, other origin, non-owner)?

Things that should *not* be in the diff: Changes to `main.py`, to existing routers, or to `test_auth.py` expectations; `GET /me`.

## Out of scope

- Switching the routers and failing start-up on missing Clerk settings → BE-063.
- `require_user` and `GET /me` → BE-064.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-062-require-principal`. Pure `resolve_principal` with the ticket's three rules, wrapped by `require_principal`; `Denied(status, detail)` rejection value maps to HTTP in one place. `require_api_key` untouched; no router uses the new dependency yet.
- `HTTPBearer(auto_error=False)` + existing `APIKeyHeader` as `Security(...)` params: both schemes will show in `/docs` once mounted (verified in the OpenAPI diff-free state for now — not mounted, per ticket).
- `get_now()` dependency pins the clock in tests; decoder/settings/clock all overridden via `dependency_overrides` on a throwaway app.
- 401s carry `WWW-Authenticate: Bearer, ApiKey`; 403 carries none. Bearer precedence: bad bearer + valid key → 401; valid bearer + wrong key → User; `Basic` scheme ignored → falls through to key.
- Echo test checks body AND headers for token/key across all 401/403/200 shapes.
- `make api-test` → 175 passed (12 new); existing `test_auth.py` untouched.
