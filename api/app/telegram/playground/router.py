"""Debugger playground router: admin-only, behind the playground switch (BE-068).

Every later playground endpoint mounts on ``playground_router`` and inherits
both guards: ``require_admin`` (401/403, BE-066) runs before
``require_playground`` (404 when off) on purpose — an anonymous caller gets
401 whether the feature is on or off, so the switch reveals nothing.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.principal import User
from app.security import require_admin
from app.settings import Settings, get_settings, playground_allowed
from app.telegram.playground.repository import record_action
from app.telegram.playground.schemas import (
    TemplateEntry,
    TemplateList,
    TemplatePreview,
    TemplateRequest,
)
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
