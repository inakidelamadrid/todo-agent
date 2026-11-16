"""Session-token port and composition (BE-060).

The signature check is the only part that needs a crypto library and a real
key, so it lives behind a function type. Everything else composes:
``verify_session`` = decode → ``check_claims``. A signature failure, a
garbled token and an unknown algorithm all arrive here as ``None`` and
become ``malformed`` — the caller never tells them apart.

Nothing is wired to this yet: the default decoder rejects every token
(fail closed) until BE-061 supplies the real RS256 adapter.
"""

from collections.abc import Callable, Mapping
from typing import Annotated, Any

from fastapi import Depends

from app.principal import ClerkRules, Rejected, User, check_claims
from app.settings import Settings, get_settings

Claims = Mapping[str, Any]
DecodeToken = Callable[[str], "Claims | None"]  # None: not a validly signed token


def reject_all(_: str) -> None:
    """Fail-closed default decoder: no token is acceptable until BE-061."""
    return None


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
    return reject_all
