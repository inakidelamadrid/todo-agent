"""API key authentication.

One shared dependency, ``require_api_key``, protects every non-public
router. Keys are supplied by clients in the ``X-API-Key`` header and
compared in constant time. Keys are never logged or echoed back.
"""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.settings import Settings, get_settings, parse_api_keys

API_KEY_HEADER_NAME = "X-API-Key"

# auto_error=False so we control the 401 body and WWW-Authenticate header.
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


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
