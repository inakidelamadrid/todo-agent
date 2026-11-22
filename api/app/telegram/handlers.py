"""Handler registry and dispatch port (BE-015).

Ports and adapters: ``Handler`` is the port the rest of the app agrees on —
a feature author implements it knowing nothing about Telegram (an
``InboundUpdate``, a ``Route``, a context; no aiogram types). Each feature
supplies an adapter and registers it in ``HANDLERS`` with one line; the
webhook never changes.

The ``Reply`` a handler returns is intent, not a sent message: BE-021
renders and sends it.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.telegram.inbound import InboundUpdate
from app.telegram.routing import Route


class Reply(BaseModel):
    """What a handler wants said back: a template name (BE-020) + data."""

    model_config = ConfigDict(frozen=True)

    template: str
    data: Mapping[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class HandlerContext:
    """What a handler may touch. ``now`` is passed in so handlers stay
    pure-testable; ``session`` ties them to the request's transaction."""

    session: AsyncSession
    now: datetime  # aware, UTC


Handler = Callable[[InboundUpdate, Route, HandlerContext], Awaitable["Reply | None"]]


async def _help(update: InboundUpdate, route: Route, ctx: HandlerContext) -> Reply:
    return Reply(template="help")


async def _unknown_command(update: InboundUpdate, route: Route, ctx: HandlerContext) -> Reply:
    return Reply(template="unknown_command", data={"command": update.command or ""})


async def _unsupported(update: InboundUpdate, route: Route, ctx: HandlerContext) -> Reply:
    return Reply(template="unsupported")


async def not_available(update: InboundUpdate, route: Route, ctx: HandlerContext) -> Reply:
    """Placeholder for targets whose feature epic has not landed yet. Keeps
    every command routable today."""
    return Reply(template="not_available")


HANDLERS: dict[str, Handler] = {
    "core.help": _help,
    "core.unknown_command": _unknown_command,
    "core.unsupported": _unsupported,
}


def resolve(target: str) -> Handler:
    """The registered handler for a route target, or ``not_available``."""
    return HANDLERS.get(target, not_available)
