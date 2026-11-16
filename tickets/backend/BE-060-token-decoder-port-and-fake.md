# BE-060: Token decoder port, `verify_session` and a fake decoder

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design (token verification is a port), §5.3
- **Assigned agent / harness / model:**
- **Depends on:** BE-059
- **Can run in parallel with:** FE-009 to FE-011
- **Public endpoint?** no
- **Review size:** ~60 lines, 3 files plus tests, ~10 min

## Goal

`api/app/session_token.py` defines the `DecodeToken` port, `verify_session(token, decode, rules, now)` which composes decoding and `check_claims`, and `get_token_decoder`, a FastAPI dependency that tests can override. A fake decoder lives in the test helpers.

## Why this ticket exists

The signature check is the only part that needs a crypto library and a real key. Putting it behind a function type, with a fake for tests, means every later ticket is tested without a key pair. BE-061 supplies the one real adapter.

## Read first

- `api/app/security.py`: the existing dependency style and how settings are injected with `Depends(get_settings)`.
- FastAPI dependency overrides: https://fastapi.tiangolo.com/advanced/testing-dependencies/
- `api/tests/conftest.py`: how fixtures and the test app are built.

## Design

- **Pattern:** Ports and adapters in its functional form: the port is a `Callable` type alias; the adapter is a function that returns one; the fake is another. Composition by passing the function in, no class.
- **Data flow:** token string → `decode(token)` → claims or `None` → `check_claims` → `User | Rejected`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/session_token.py` (new):

```python
from collections.abc import Callable, Mapping
from typing import Annotated, Any
from fastapi import Depends
from app.principal import ClerkRules, Rejected, User, check_claims
from app.settings import Settings, get_settings

Claims = Mapping[str, Any]
DecodeToken = Callable[[str], Claims | None]   # None: not a validly signed token

def reject_all(_: str) -> None:               # fail-closed default until BE-061
    return None

def verify_session(token: str, decode: DecodeToken, rules: ClerkRules, now: int) -> User | Rejected:
    claims = decode(token)
    if claims is None:
        return Rejected("malformed")
    return check_claims(claims, rules, now)

def get_token_decoder(settings: Annotated[Settings, Depends(get_settings)]) -> DecodeToken:
    return reject_all
```

- `api/tests/fakes.py` (new): `fake_decoder(table: Mapping[str, Claims]) -> DecodeToken` returns the claims for known tokens, `None` for anything else; `make_claims(**overrides) -> dict` builds a valid claim set (`sub='user_owner'`, `azp='http://localhost:5173'`, `exp` far in the future) for tests to tweak.
- `api/tests/test_session_token.py` (new).

`get_token_decoder` rejects everything on purpose: the app cannot accept a Clerk token until BE-061 gives it a real adapter, and nothing is wired to it yet.

A signature failure, a garbled token and an unknown algorithm all arrive here as `None` and become `malformed`. The caller does not need to tell them apart.

## Steps

1. Write `session_token.py`.
2. Write `fakes.py` and the tests.
3. Run `make api-test`.

## Tests

- `test_verify_session_returns_user_for_a_known_good_token`: fake decoder + valid claims → `User`.
- `test_verify_session_unknown_token_is_malformed`: decoder returns `None` → `Rejected('malformed')`.
- `test_verify_session_passes_claim_rejections_through`: expired claims → `Rejected('expired')`; non-owner → `not_owner`.
- `test_default_decoder_rejects_everything`: `get_token_decoder(settings)('anything')` is `None`.
- `test_decoder_dependency_can_be_overridden`: a tiny app using `Depends(get_token_decoder)` with `dependency_overrides` sees the fake.

## Acceptance criteria

- [ ] `DecodeToken`, `verify_session` and `get_token_decoder` exist as specified
- [ ] The default decoder rejects every token (fail closed)
- [ ] `tests/fakes.py` offers `fake_decoder` and `make_claims`, and no test needs a real key
- [ ] No new dependency
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_session_token.py -q`: green.
2. Confirm nothing imports `session_token` from `main.py` yet: `grep -n session_token api/app/main.py` prints nothing.

## Review guide

Read the diff in this order, and check:

1. `api/app/session_token.py`: is `verify_session` only composition (no logic of its own beyond `None`)?
2. `api/tests/fakes.py`: could a test misuse it to pass an invalid token by accident?
3. Is the default decoder really closed?

Things that should *not* be in the diff: `jwt`, a key, the Clerk settings used for anything, a route, `main.py` edits.

## Out of scope

- The real RS256 decoder → BE-061.
- Using this in a dependency that reads headers → BE-062.

## Notes / log

The agent adds progress notes, decisions and open questions here.
