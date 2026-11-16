"""Authentication: API keys for machines, Clerk session tokens for people.

``require_api_key`` (BE-001) protects every non-public router until BE-063
swaps routers to ``require_principal`` (BE-062), which accepts either kind
of caller. Keys and tokens are never logged or echoed back.

The decision logic is a pure resolver (``resolve_principal``) wrapped in a
thin FastAPI dependency: rejections are values mapped to HTTP in exactly
one place.
"""

import secrets
import time
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.principal import ClerkRules, Machine, Principal, User
from app.session_token import DecodeToken, get_token_decoder, verify_session
from app.settings import Settings, get_settings, parse_api_keys, parse_csv

API_KEY_HEADER_NAME = "X-API-Key"

# auto_error=False so we control the 401 body and WWW-Authenticate header.
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

MACHINE_LABEL = "api-key"  # placeholder until F-2 names keys

DETAIL_INVALID = "Invalid or missing credentials"
DETAIL_NOT_ALLOWED = "Not allowed"
_CHALLENGES = {"WWW-Authenticate": "Bearer, ApiKey"}


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def _matches_any(provided: str, valid_keys: tuple[str, ...]) -> bool:
    """Constant-time comparison against every configured key."""
    return any(secrets.compare_digest(provided, key) for key in valid_keys)


def require_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """FastAPI dependency: reject requests without a valid API key."""
    if api_key is None or not _matches_any(api_key, parse_api_keys(settings.api_keys)):
        raise _unauthorized()


# --- People and machines (BE-062) ------------------------------------------


@dataclass(frozen=True)
class Denied:
    """A rejection as a value; the dependency maps it to HTTP in one place."""

    status: int  # 401 or 403
    detail: str


def _bearer_token(authorization: str | None) -> str | None:
    """The token of a Bearer authorization; other schemes are ignored."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def resolve_principal(
    authorization: str | None,
    api_key: str | None,
    *,
    valid_keys: tuple[str, ...],
    decode: DecodeToken,
    rules: ClerkRules,
    now: int,
) -> "Principal | Denied":
    """Pure: who is calling, or why not. First rule that applies wins:

    1. A Bearer token wins over any API key sent with it (a bad bearer is
       never rescued by a valid key). not_owner → 403, any other
       rejection → 401.
    2. A valid ``X-API-Key`` → ``Machine``.
    3. Anything else → 401.
    """
    token = _bearer_token(authorization)
    if token is not None:
        result = verify_session(token, decode, rules, now)
        if isinstance(result, User):
            return result
        if result.reason == "not_owner":
            return Denied(status.HTTP_403_FORBIDDEN, DETAIL_NOT_ALLOWED)
        return Denied(status.HTTP_401_UNAUTHORIZED, DETAIL_INVALID)
    if api_key is not None and _matches_any(api_key, valid_keys):
        return Machine(key_label=MACHINE_LABEL)
    return Denied(status.HTTP_401_UNAUTHORIZED, DETAIL_INVALID)


def get_now() -> int:
    """Clock as its own dependency so tests can pin time."""
    return int(time.time())


def require_principal(
    bearer: Annotated[HTTPAuthorizationCredentials | None, Security(http_bearer)],
    api_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
    decode: Annotated[DecodeToken, Depends(get_token_decoder)],
    now: Annotated[int, Depends(get_now)],
) -> Principal:
    """FastAPI dependency: a ``User`` for the owner's session, a ``Machine``
    for a valid API key; 401 with both challenges otherwise, 403 for a valid
    token from someone else."""
    authorization = f"Bearer {bearer.credentials}" if bearer is not None else None
    rules = ClerkRules(
        authorized_parties=parse_csv(settings.clerk_authorized_parties),
        allowed_user_ids=parse_csv(settings.clerk_allowed_user_ids),
    )
    result = resolve_principal(
        authorization,
        api_key,
        valid_keys=parse_api_keys(settings.api_keys),
        decode=decode,
        rules=rules,
        now=now,
    )
    if isinstance(result, Denied):
        headers = _CHALLENGES if result.status == status.HTTP_401_UNAUTHORIZED else None
        raise HTTPException(
            status_code=result.status, detail=result.detail, headers=headers
        )
    return result
