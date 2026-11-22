"""Pure routing: where an update goes (BE-013).

One routing table, easy to extend when a new epic adds a command: a
dictionary plus one pure function, no I/O, no settings, no clock. Pending
mode (BE-016) and caption keywords (BE-014) slot into this order later.

Naming: ``webhook.py`` is the FastAPI route; this module is the pure
decision the epic calls "the router".
"""

from types import MappingProxyType
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict

from app.telegram.inbound import InboundUpdate, UpdateKind

RouteKind = Literal["callback", "command", "pending", "keyword", "default", "unsupported"]


class Route(BaseModel):
    """The routing decision, frozen. ``target`` is ``<feature>.<action>``."""

    model_config = ConfigDict(frozen=True)

    kind: RouteKind
    target: str
    arg: str = ""  # callback argument (filled by BE-023)


# The single place a new command is added. MappingProxyType: not mutable.
COMMANDS: Mapping[str, str] = MappingProxyType(
    {
        "help": "core.help",
        "start": "core.start",
        "undo": "core.undo",
        "pause": "notifications.pause",
        "resume": "notifications.resume",
        "now": "tasks.now",
        "inbox": "inbox.count",
        "done": "tasks.done",
        "today": "expenses.today",
        "month": "expenses.month",
        "radar": "radar.show",
        "reset": "reset.start",
        "vault": "vault.await_upload",
    }
)


def route(update: InboundUpdate) -> Route:
    """Decide the route, in this order: callback, command, then defaults.

    Read top to bottom; each kind maps to exactly one target today.
    """
    if update.kind is UpdateKind.CALLBACK:
        # BE-023 verifies the data and replaces the target with the action.
        return Route(kind="callback", target="callback.unverified")
    if update.kind is UpdateKind.COMMAND:
        return Route(
            kind="command",
            target=COMMANDS.get(update.command or "", "core.unknown_command"),
        )
    if update.kind in (UpdateKind.TEXT, UpdateKind.VOICE):
        return Route(kind="default", target="braindump.capture")
    if update.kind in (UpdateKind.PHOTO, UpdateKind.DOCUMENT):
        return Route(kind="default", target="media.classify")
    return Route(kind="unsupported", target="core.unsupported")
