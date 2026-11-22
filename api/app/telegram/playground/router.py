"""Debugger playground router: admin-only, behind the playground switch (BE-068).

Every later playground endpoint mounts on ``playground_router`` and inherits
both guards: ``require_admin`` (401/403, BE-066) runs before
``require_playground`` (404 when off) on purpose — an anonymous caller gets
401 whether the feature is on or off, so the switch reveals nothing.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.principal import User
from app.security import require_admin
from app.settings import Settings, get_settings, playground_allowed
from app.telegram import service
from app.telegram.aiogram_sender import get_sender
from app.telegram.handlers import Reply
from app.telegram.playground.limits import TEST_MESSAGES_PER_HOUR, may_send
from app.telegram.playground.repository import count_actions_since, record_action
from app.telegram.playground.schemas import (
    TemplateEntry,
    TemplateList,
    TemplatePreview,
    TemplateRequest,
    TestMessageSent,
)
from app.telegram.sender import SendFailed, TelegramNotConfigured, TelegramSender
from app.telegram.templates import MissingTemplateData, UnknownTemplate, list_templates, render


def require_playground(
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """404 when the playground is off: a switched-off feature does not exist."""
    if not playground_allowed(settings):
        raise HTTPException(status_code=404, detail="Not found")


class PlaygroundInfo(BaseModel):
    """Probe answer proving both guards passed; no data besides the flag."""

    enabled: bool = True


playground_router = APIRouter(
    prefix="/admin/telegram",
    tags=["telegram-playground"],
    dependencies=[Depends(require_admin), Depends(require_playground)],
    # The public schema reveals nothing: these routes never appear in
    # openapi.json or /docs, in any environment (the guards still run).
    include_in_schema=False,
)


@playground_router.get("/playground", response_model=PlaygroundInfo)
def probe() -> PlaygroundInfo:
    return PlaygroundInfo()


@playground_router.get("/templates", response_model=TemplateList)
def templates() -> TemplateList:
    return TemplateList(
        templates=tuple(TemplateEntry(name=t.name, fields=t.fields) for t in list_templates())
    )


def _render_or_http_error(body: TemplateRequest) -> str:
    """The real ``render``, its errors as HTTP errors (shared with BE-079)."""
    try:
        return render(body.template, body.data)
    except UnknownTemplate:
        raise HTTPException(status_code=404, detail="Unknown template") from None
    except MissingTemplateData as error:
        raise HTTPException(status_code=422, detail=f"Missing field: {error.field}") from None
    except ValueError:
        raise HTTPException(status_code=422, detail="Rendered text is longer than 4096 characters") from None


@playground_router.post("/templates/preview", response_model=TemplatePreview)
async def preview(
    body: TemplateRequest,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TemplatePreview:
    """Render only; nothing is sent. Every attempt is recorded, and committed
    before a rejection is raised (the request session rolls back on error)."""
    try:
        text = _render_or_http_error(body)
    except HTTPException:
        await record_action(session, admin.user_id, "template_preview", "rejected")
        await session.commit()
        raise
    await record_action(session, admin.user_id, "template_preview", "ok")
    return TemplatePreview(html=text, length=len(text))


async def _record_and_raise(
    session: AsyncSession, admin: User, outcome: str, error: HTTPException
) -> NoReturn:
    """Record a refused attempt and commit it before raising: the request
    session rolls back on error, and every attempt must be on record."""
    await record_action(session, admin.user_id, "test_message", outcome)
    await session.commit()
    raise error


@playground_router.post("/test-message", response_model=TestMessageSent)
async def test_message(
    body: TemplateRequest,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    sender: Annotated[TelegramSender, Depends(get_sender)],
) -> TestMessageSent:
    """Send ``body.template`` to the allowlisted chat now (BE-079): no queue,
    no policy, like a reply. The recipient comes from settings only."""
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    if not may_send(await count_actions_since(session, "test_message", since)):
        detail = f"Test message limit reached ({TEST_MESSAGES_PER_HOUR} per hour)"
        await _record_and_raise(session, admin, "rejected", HTTPException(429, detail))
    try:
        _render_or_http_error(body)
    except HTTPException as error:
        await _record_and_raise(session, admin, "rejected", error)
    chat_id = settings.telegram_allowed_user_id
    if chat_id is None:
        await _record_and_raise(
            session, admin, "failed", HTTPException(409, "TELEGRAM_ALLOWED_USER_ID is not set")
        )
    try:
        sent = await service.reply(sender, chat_id, Reply(template=body.template, data=body.data))
    except TelegramNotConfigured:
        await _record_and_raise(
            session, admin, "failed", HTTPException(409, "TELEGRAM_BOT_TOKEN is not set")
        )
    except SendFailed as error:
        detail = f"Telegram refused the message ({type(error).__name__})"
        await _record_and_raise(session, admin, "failed", HTTPException(502, detail))
    await record_action(session, admin.user_id, "test_message", "ok")
    return TestMessageSent(message_id=sent.message_id)
