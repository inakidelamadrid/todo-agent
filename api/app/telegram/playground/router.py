"""Debugger playground router: admin-only, behind the playground switch (BE-068).

Every later playground endpoint mounts on ``playground_router`` and inherits
both guards: ``require_admin`` (401/403, BE-066) runs before
``require_playground`` (404 when off) on purpose — an anonymous caller gets
401 whether the feature is on or off, so the switch reveals nothing.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.security import require_admin
from app.settings import Settings, get_settings, playground_allowed


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
)


@playground_router.get("/playground", response_model=PlaygroundInfo)
def probe() -> PlaygroundInfo:
    return PlaygroundInfo()
