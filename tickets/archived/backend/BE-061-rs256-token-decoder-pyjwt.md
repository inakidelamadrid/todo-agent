# BE-061: Real token decoder: RS256 signature check with PyJWT

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design, §5.3, §7 Security
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** BE-058, BE-060
- **Can run in parallel with:** FE-009 to FE-011
- **Public endpoint?** no
- **Review size:** ~45 lines, 3 files plus tests, ~12 min

## Goal

`make_rs256_decoder(public_key_pem)` returns a `DecodeToken` that verifies an RS256 signature with the Clerk instance's public key, without any network call, and `get_token_decoder` now returns it when Clerk is configured.

## Why this ticket exists

This is the only ticket that touches a crypto library, so it is kept tiny and isolated. It checks the signature and nothing else: expiry, origin and owner stay in `check_claims`, where a fake clock can test them.

## Read first

- `api/app/session_token.py` (BE-060): the port this implements.
- PyJWT usage: https://pyjwt.readthedocs.io/en/stable/usage.html and the algorithms page (why the allowed algorithm list matters).
- Clerk 'Manual JWT verification' (token shape, `azp`, `nbf`): https://clerk.com/docs/backend-requests/manual-jwt

## Design

- **Pattern:** Adapter behind a port: a factory function returns the decoder closure. No class.
- **Data flow:** `Authorization` token → `jwt.decode` (signature only) → claims dict, or `None` on any `PyJWTError`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `pyjwt[crypto]` 2.15.1 | **new** | RS256 signature verification | MIT, released 2026-09-28, Python ≥ 3.9. Hand-rolling JWT is on the 'never hand-write' list. The `crypto` extra pulls `cryptography` (50.x), which RS256 needs. Alternative considered: `clerk-backend-api`, rejected (owner answer): heavy SDK, takes an `httpx.Request`, not a pure function |

## Details

**Install:** `cd api && uv add "pyjwt[crypto]"`. Re-run the registry check first (`curl -s https://pypi.org/pypi/pyjwt/json`) and use the version it prints. It is the only dependency in this ticket and installing it is an acceptance criterion.

**Security notes for the reviewer**

- `algorithms=["RS256"]` is pinned. Without a pinned list, a token signed with `HS256` using the public key as its secret, or `alg: none`, is the classic bypass. Both are tested.
- Expiry, not-before, audience and issuer verification are switched off inside PyJWT on purpose (`options={"verify_exp": False, "verify_nbf": False, "verify_aud": False, "verify_iss": False, "verify_iat": False}`), because `check_claims` owns them and takes `now` as an argument. The signature check stays on.
- Any `jwt.PyJWTError` becomes `None`. Nothing about the token is logged.

**Files**

- `api/app/session_token.py` (changed): add

```python
import jwt

def make_rs256_decoder(public_key_pem: str) -> DecodeToken:
    def decode(token: str) -> Claims | None:
        try:
            return jwt.decode(token, public_key_pem, algorithms=["RS256"], options={...})
        except jwt.PyJWTError:
            return None
    return decode
```

  and change `get_token_decoder` to: if the key is empty return `reject_all`, otherwise `make_rs256_decoder(normalize_pem(settings.clerk_jwt_public_key))`, cached by key string with `functools.cache` on a small helper so the PEM is not rebuilt per request.
- `api/pyproject.toml` and `api/uv.lock` (changed by `uv add`).
- `api/tests/test_rs256_decoder.py` (new): an RSA key pair is generated in a fixture with `cryptography` (never a real Clerk key).

**Open point to settle by hand later:** Clerk's session token claim names (`azp`, `nbf`) are taken from its docs. FE-013's hand check confirms a real token passes `check_claims`.

## Steps

1. Run the registry check and `uv add "pyjwt[crypto]"`.
2. Write the key-pair fixture and the tests below, red first.
3. Add `make_rs256_decoder`, then switch `get_token_decoder`.
4. Run `make api-test`.

## Tests

- `test_valid_signature_returns_claims`: token signed with the private key decodes to its claims.
- `test_wrong_key_signature_returns_none`: signed by a different key pair → `None`.
- `test_tampered_payload_returns_none`: change one character of the payload → `None`.
- `test_hs256_signed_with_public_key_returns_none`: algorithm-confusion attempt → `None`.
- `test_alg_none_returns_none`: unsigned token → `None`.
- `test_garbage_returns_none`: `'not.a.jwt'`, `''` → `None`.
- `test_expired_token_still_decodes`: expiry is not this function's job → claims returned.
- `test_get_token_decoder_is_closed_when_key_is_empty` and `test_get_token_decoder_accepts_configured_key`.

## Acceptance criteria

- [x] `pyjwt[crypto]` is installed with `uv add`, and the version matches the registry check
- [x] `make_rs256_decoder` pins RS256 and returns `None` for wrong-key, tampered, `HS256`, `none` and garbage tokens
- [x] No network call happens per request (the key comes from settings)
- [x] `get_token_decoder` stays closed when `CLERK_JWT_PUBLIC_KEY` is empty
- [x] Tests use generated keys only, and no token or key appears in any log or test output
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_rs256_decoder.py -q`: green.
2. `git diff api/pyproject.toml`: exactly one new dependency line.
3. `grep -rn "print\|logging" api/app/session_token.py`: nothing.

## Review guide

Read the diff in this order, and check:

1. `api/app/session_token.py`: is the algorithm list pinned, and are exactly the time and audience checks off?
2. The tests: do the attack cases (`HS256`, `none`) really build the forged token the way an attacker would?
3. `api/pyproject.toml`: one dependency, nothing else moved.

Things that should *not* be in the diff: Any check of `exp`, `azp` or `sub` (that is `check_claims`), a route, a header read, a Clerk SDK.

## Out of scope

- Reading the header and mapping to `401`/`403` → BE-062.
- Making the settings mandatory → BE-063.

## Assumptions

- Clerk session tokens carry `sub`, `exp`, `nbf` and `azp`, as its docs say. Confirmed against a real token in FE-013's hand check.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-061-rs256-token-decoder` from main (BE-058 + BE-060 merged). Registry re-check: **PyJWT 2.15.1, MIT** — matches the ticket's evaluation; `uv add "pyjwt[crypto]"` pulled `cryptography 50.0.2`.
- `make_rs256_decoder`: pinned `algorithms=["RS256"]`; only `verify_exp/nbf/aud/iss/iat` off (signature stays on); every `PyJWTError` → `None`; no logging of tokens.
- `get_token_decoder`: empty key → `reject_all` (closed); else `_cached_decoder` (functools.cache keyed by normalized PEM) so the key is wrapped once per process.
- **Testing detail worth reviewing:** PyJWT refuses to *encode* an HS256 token with a PEM-looking key (built-in asymmetric-key guard), so the algorithm-confusion forgery is handcrafted in the test with `hmac`+`base64url` — the way an attacker actually builds it.
- Boundary verified: `test_expired_token_still_decodes` proves expiry stays out of this layer; one-line `\n` PEM works end-to-end via `test_get_token_decoder_accepts_configured_key`; cached decoder returns the identical object per key.
- `make api-test` → 163 passed (13 new); `git diff api/pyproject.toml` shows exactly one dependency line; no `print`/`logging` in `session_token.py`.
