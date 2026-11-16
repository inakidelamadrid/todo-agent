"""Session-token port and composition (BE-060, RS256 adapter BE-061).

The signature check is the only part that needs a crypto library and a real
key, so it lives behind a function type. Everything else composes:
``verify_session`` = decode → ``check_claims``. A signature failure, a
garbled token and an unknown algorithm all arrive here as ``None`` and
become ``malformed`` — the caller never tells them apart.

Expiry, not-before, audience and issuer stay OFF inside PyJWT on purpose:
``check_claims`` owns them and takes ``now`` as an argument. The signature
check stays on, RS256 is the only acceptable algorithm, and nothing about a
token is ever logged. When no Clerk public key is configured, the decoder
fails closed (rejects everything).
"""

import functools
from collections.abc import Callable, Mapping
from typing import Annotated, Any

import jwt
from fastapi import Depends

from app.principal import ClerkRules, Rejected, User, check_claims
from app.settings import Settings, get_settings, normalize_pem

Claims = Mapping[str, Any]
DecodeToken = Callable[[str], "Claims | None"]  # None: not a validly signed token

# Only the time/audience/issuer checks are off (check_claims owns them);
# the signature check stays on. Pinning RS256 blocks the classic bypasses:
# HS256 signed with the public key as secret, and alg=none.
_JWT_OPTIONS: dict[str, bool] = {
    "verify_exp": False,
    "verify_nbf": False,
    "verify_aud": False,
    "verify_iss": False,
    "verify_iat": False,
}


def reject_all(_: str) -> None:
    """Fail-closed default decoder: no token is acceptable without a key."""
    return None


def make_rs256_decoder(public_key_pem: str) -> DecodeToken:
    """Adapter: verify RS256 with the Clerk instance's public key, locally."""

    def decode(token: str) -> "Claims | None":
        try:
            return jwt.decode(
                token, public_key_pem, algorithms=["RS256"], options=_JWT_OPTIONS
            )
        except jwt.PyJWTError:
            return None

    return decode


@functools.cache
def _cached_decoder(public_key_pem: str) -> DecodeToken:
    """One decoder per key value, so the PEM is wrapped once per process."""
    return make_rs256_decoder(public_key_pem)


def verify_session(
    token: str, decode: DecodeToken, rules: ClerkRules, now: int
) -> "User | Rejected":
    """Decode then check. The only logic here: undecodable means malformed."""
    claims = decode(token)
    if claims is None:
        return Rejected("malformed")
    return check_claims(claims, rules, now)


def get_token_decoder(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DecodeToken:
    """FastAPI dependency; tests override it (dependency_overrides)."""
    normalized = normalize_pem(settings.clerk_jwt_public_key)
    if not normalized:
        return reject_all
    return _cached_decoder(normalized)
