"""Telegram webhook secret guard (BE-007).

The webhook is the first endpoint not protected by an API key: Telegram
cannot send ours, so it echoes back the secret we registered via
``setWebhook``. This dependency is the twin of ``app.security.require_api_key``
and fails closed: an unconfigured server rejects everything.

The provided and expected values are never logged or echoed — the error
detail names neither.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.settings import Settings, get_settings

TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
DETAIL_INVALID_SECRET = "Invalid or missing Telegram secret"


def require_telegram_secret(
    settings: Annotated[Settings, Depends(get_settings)],
    provided: Annotated[str | None, Header(alias=TELEGRAM_SECRET_HEADER)] = None,
) -> None:
    """Reject unless the header matches the configured webhook secret."""
    expected = settings.telegram_webhook_secret.get_secret_value()
    if provided is None or not expected or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=DETAIL_INVALID_SECRET,
        )
