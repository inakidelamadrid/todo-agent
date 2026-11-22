"""Telegram webhook route (BE-008): guard → parse → ack.

The skeleton every inbound ticket hangs on. Telegram retries a delivery
whenever the response is not 2xx, so this route answers ``200`` even for
payloads it cannot use; a non-2xx is only for requests that are not from
Telegram at all. There is no behaviour here yet.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.settings import Settings, get_settings
from app.telegram import repository
from app.telegram.allowlist import is_allowed
from app.telegram.inbound import parse_inbound
from app.telegram.security import require_telegram_secret

logger = logging.getLogger(__name__)


class WebhookAck(BaseModel):
    """Frozen `200 {"ok": true}` — Telegram only needs to stop retrying."""

    model_config = ConfigDict(frozen=True)

    ok: bool = True


telegram_webhook_router = APIRouter(
    prefix="/integrations/telegram",
    tags=["telegram"],
    dependencies=[Depends(require_telegram_secret)],
)


@telegram_webhook_router.post("/webhook", include_in_schema=False)
async def receive_update(
    payload: dict[str, Any],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WebhookAck:
    """Order matters and must stay: secret (router dep) → parse → allowlist →
    claim. A stranger's update never reaches the database; a duplicate
    delivery is acknowledged and dropped before any work happens (BE-012)."""
    ack = WebhookAck()
    try:
        inbound = parse_inbound(payload)
    except ValidationError:
        # One warning line, no payload content: bodies are user data.
        logger.warning("telegram.unparseable")
        return ack
    if not is_allowed(inbound, settings.telegram_allowed_user_id):
        # Counter line only: no user/chat ID, no text — a stranger must not
        # be able to tell the bot exists, and logs carry no identifiers.
        logger.info("telegram.ignored")
        return ack
    if not await repository.claim_update(session, inbound):
        return ack  # duplicate delivery: already handled exactly once
    # BE-015 inserts dispatch here.
    await repository.mark_update(session, inbound.update_id, "processed")
    return ack
