"""Principal types and the pure token-claim checks (BE-059).

The heart of EPIC-009: every rule about whether a token's claims are
acceptable, as a pure function. No JWT library (that's BE-061), no clock
(``now`` is an argument), no settings object (rules come in as a
``ClerkRules`` value). Returns a value — never raises — so the caller
(BE-062) decides what each reason means for HTTP.

JWT claims in plain words: ``sub`` = who the token is about, ``exp`` =
expires at, ``nbf`` = not valid before, ``azp`` = the origin that asked for
the token. ``iss`` is not checked: the signature from this instance's key
already ties the token to this Clerk instance.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

LEEWAY_SECONDS = 5


@dataclass(frozen=True)
class User:
    user_id: str  # Clerk `sub`


@dataclass(frozen=True)
class Machine:
    key_label: str  # which API key; a fixed placeholder until F-2 names keys


Principal = User | Machine


def is_admin(principal: Principal, admin_user_ids: tuple[str, ...]) -> bool:
    """True only for a User whose user_id is in the admin list."""
    return isinstance(principal, User) and principal.user_id in admin_user_ids

RejectionReason = Literal[
    "malformed", "expired", "not_yet_valid", "wrong_party", "not_owner"
]


@dataclass(frozen=True)
class Rejected:
    reason: RejectionReason


@dataclass(frozen=True)
class ClerkRules:
    authorized_parties: tuple[str, ...]
    allowed_user_ids: tuple[str, ...]


def _is_int(value: Any) -> bool:
    # JSON booleans are ints in Python; a claim `true` is not a timestamp.
    return isinstance(value, int) and not isinstance(value, bool)


def check_claims(
    claims: Mapping[str, Any], rules: ClerkRules, now: int
) -> User | Rejected:
    """Decide whether token claims identify the owner. First failure wins.

    Order: malformed → expired → not_yet_valid → wrong_party → not_owner.
    Both rule tuples empty rejects everyone (fail closed).
    """
    sub = claims.get("sub")
    exp = claims.get("exp")
    azp = claims.get("azp")
    nbf = claims.get("nbf")

    if (
        not isinstance(sub, str)
        or not sub.strip()
        or not _is_int(exp)
        or not isinstance(azp, str)
        or not azp.strip()
        or (nbf is not None and not _is_int(nbf))
    ):
        return Rejected("malformed")

    if exp + LEEWAY_SECONDS <= now:
        return Rejected("expired")

    if nbf is not None and nbf - LEEWAY_SECONDS > now:
        return Rejected("not_yet_valid")

    if azp not in rules.authorized_parties:
        return Rejected("wrong_party")

    if sub not in rules.allowed_user_ids:
        return Rejected("not_owner")

    return User(user_id=sub)
