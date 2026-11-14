"""Public endpoints — the only routes reachable without an API key.

A route is public only when a ticket explicitly says so; everything else
lives on routers protected by ``require_api_key``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.settings import Settings, get_settings

router = APIRouter(tags=["public"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    version: str


class PingResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    ping: str


@router.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version)


@router.get("/ping")
def ping() -> PingResponse:
    return PingResponse(ping="pong")
