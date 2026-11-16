# BE-059: `Principal` types and the pure token-claim checks

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.3 Principal and dependency, §5.4 Owner allowlist
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-058, FE-009
- **Public endpoint?** no
- **Review size:** ~90 lines, 2 files plus tests, ~12 min

## Goal

`api/app/principal.py` defines `User`, `Machine`, `Principal` and the pure function `check_claims(claims, rules, now)`, which returns a `User` or a typed rejection.

## Why this ticket exists

This is the heart of the epic and the part worth reading slowly: every decision about whether a token is acceptable, as a pure function with no JWT library, no clock and no settings object. Because it takes `now` as a number and the rules as a value, tests can pin every edge of `exp`, `nbf`, `azp` and the owner check.

## Read first

- `api/app/bills/domain.py`: how pure rules are written and tested here.
- JWT claims in plain words: `sub` = who the token is about, `exp` = expires at, `nbf` = not valid before, `azp` = the origin that asked for the token (RFC 7519 §4.1; Clerk adds `azp`).
- `api/tests/test_bills_domain.py`: table-style tests to imitate.

## Design

- **Pattern:** Tagged union (sum type) with frozen dataclasses, and 'result as a value': the function returns `User | Rejected` instead of raising, so the caller decides what each reason means.
- **Data flow:** claims (a dict) + `ClerkRules` + `now` → `check_claims` → `User(user_id)` or `Rejected(reason)`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/principal.py` (new). Standard library only.

```python
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

@dataclass(frozen=True)
class User:
    user_id: str            # Clerk `sub`

@dataclass(frozen=True)
class Machine:
    key_label: str          # which API key; a fixed placeholder until F-2 names keys

Principal = User | Machine

RejectionReason = Literal["malformed", "expired", "not_yet_valid", "wrong_party", "not_owner"]

@dataclass(frozen=True)
class Rejected:
    reason: RejectionReason

@dataclass(frozen=True)
class ClerkRules:
    authorized_parties: tuple[str, ...]
    allowed_user_ids: tuple[str, ...]

LEEWAY_SECONDS = 5

def check_claims(claims: Mapping[str, Any], rules: ClerkRules, now: int) -> User | Rejected: ...
```

**Order of checks** (the first failure wins):

1. `malformed`: `sub` is not a non-empty string, or `exp` is not an int (a `bool` is not an int here), or `azp` is not a non-empty string. `nbf` may be absent; if present it must be an int.
2. `expired`: `exp + LEEWAY_SECONDS <= now`.
3. `not_yet_valid`: `nbf` present and `nbf - LEEWAY_SECONDS > now`.
4. `wrong_party`: `azp` is not in `rules.authorized_parties`.
5. `not_owner`: `sub` is not in `rules.allowed_user_ids`.
6. Otherwise `User(user_id=sub)`.

Both tuples empty means every token is rejected (`wrong_party`, then `not_owner`): fail closed.

**Notes**

- `iss` is not checked: the signature from this instance's key (BE-061) already ties the token to this Clerk instance.
- The reasons are values for the caller to map. This ticket decides nothing about HTTP.
- Nothing here reads a header, a clock or the environment.

## Steps

1. Write the dataclasses and `check_claims` with `malformed` only, test, then add each check in the order above with its tests.
2. Run `make api-test`.

## Tests

- `test_valid_claims_return_user`: all good → `User('user_1')`.
- `test_missing_or_blank_sub_is_malformed`, `test_missing_exp_is_malformed`, `test_exp_as_string_is_malformed`, `test_bool_exp_is_malformed`, `test_missing_azp_is_malformed`.
- `test_expired_token_is_rejected` and `test_token_inside_leeway_is_still_valid`: boundary at `exp + 5`.
- `test_nbf_in_the_future_is_not_yet_valid` and `test_missing_nbf_is_fine`.
- `test_azp_not_listed_is_wrong_party`.
- `test_sub_not_listed_is_not_owner`.
- `test_empty_rules_reject_everyone`.
- `test_check_order_expired_beats_wrong_party`: a token with two problems reports the first in the order.
- `test_principal_types_are_frozen`: assigning a field raises `FrozenInstanceError`.

## Acceptance criteria

- [ ] `User`, `Machine`, `Principal`, `Rejected`, `ClerkRules` and `check_claims` exist as specified
- [ ] `check_claims` is pure: it takes `now` and `rules` as arguments, and touches no clock, header or environment
- [ ] Every rejection reason has a test, and the boundary of `exp` and `nbf` is tested on both sides
- [ ] Empty rules reject everyone
- [ ] No new dependency
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_principal.py -q`: green.
2. `grep -n "import" api/app/principal.py`: only `collections.abc`, `dataclasses`, `typing`.

## Review guide

Read the diff in this order, and check:

1. `api/app/principal.py`: is the order of checks the one written above, and is anything unreachable?
2. Does `check_claims` return values, never raise?
3. `api/tests/test_principal.py`: is each boundary hit exactly (equal to, one second either side)?

Things that should *not* be in the diff: Any `jwt` import, `time.time()`, `os.environ`, FastAPI, HTTP status codes.

## Out of scope

- Verifying the signature → BE-061.
- Deciding which reason becomes `401` or `403` → BE-062.

## Notes / log

The agent adds progress notes, decisions and open questions here.
