"""Tests for the pure router (BE-013).

Every recorded payload from BE-005 routes somewhere predictable; the command
table is exercised by parameter so adding a command without a test fails.
"""

import pytest

from app.telegram.inbound import InboundUpdate, UpdateKind, to_inbound
from app.telegram.routing import COMMANDS, Route, route
from tests.telegram_fixtures import load_update


def _command(name: str) -> InboundUpdate:
    return InboundUpdate(update_id=1, kind=UpdateKind.COMMAND, command=name)


@pytest.mark.parametrize("command,target", sorted(COMMANDS.items()))
def test_every_listed_command_routes_to_its_target(command: str, target: str) -> None:
    assert route(_command(command)) == Route(kind="command", target=target)


def test_commands_table_holds_all_thirteen_plus_start() -> None:
    assert len(COMMANDS) == 13


def test_unknown_command_routes_to_unknown_command() -> None:
    assert route(_command("fly")).target == "core.unknown_command"


def test_text_and_voice_default_to_braindump() -> None:
    for kind in (UpdateKind.TEXT, UpdateKind.VOICE):
        update = InboundUpdate(update_id=1, kind=kind)
        assert route(update) == Route(kind="default", target="braindump.capture")


def test_photo_and_document_default_to_classify() -> None:
    for kind in (UpdateKind.PHOTO, UpdateKind.DOCUMENT):
        update = InboundUpdate(update_id=1, kind=kind)
        assert route(update) == Route(kind="default", target="media.classify")


def test_callback_wins_over_everything() -> None:
    update = InboundUpdate(
        update_id=1,
        kind=UpdateKind.CALLBACK,
        command="help",  # cannot exist in practice; callback still wins
        callback_data="x",
    )
    assert route(update) == Route(kind="callback", target="callback.unverified")


def test_unsupported_update() -> None:
    update = InboundUpdate(update_id=1, kind=UpdateKind.UNSUPPORTED)
    assert route(update) == Route(kind="unsupported", target="core.unsupported")


def test_commands_table_is_immutable() -> None:
    with pytest.raises(TypeError):
        COMMANDS["new"] = "x.y"  # type: ignore[index]


# --- every recorded payload routes -------------------------------------------


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("text", Route(kind="default", target="braindump.capture")),
        ("command", Route(kind="command", target="core.help")),
        ("voice", Route(kind="default", target="braindump.capture")),
        ("photo", Route(kind="default", target="media.classify")),
        ("document", Route(kind="default", target="media.classify")),
        ("callback_query", Route(kind="callback", target="callback.unverified")),
        ("stranger_text", Route(kind="default", target="braindump.capture")),
    ],
)
def test_every_fixture_routes(fixture: str, expected: Route) -> None:
    assert route(to_inbound(load_update(fixture))) == expected
