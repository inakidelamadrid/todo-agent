"""Telegram webhook route (BE-008): guard → parse → ack.

The skeleton every inbound ticket hangs on. Telegram retries a delivery
whenever the response is not 2xx, so this route answers ``200`` even for
payloads it cannot use; a non-2xx is only for requests that are not from
Telegram at all. There is no behaviour here yet.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, ValidationError

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
async def receive_update(payload: dict[str, Any]) -> WebhookAck:
    ack = WebhookAck()
    try:
        parse_inbound(payload)
    except ValidationError:
        # One warning line, no payload content: bodies are user data.
        logger.warning("telegram.unparseable")
    return ack
