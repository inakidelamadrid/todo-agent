"""Message templates and central escaping (BE-020)."""

import asyncio

import pytest

from app.telegram import templates
from app.telegram.handlers import HANDLERS, not_available
from app.telegram.routing import COMMANDS
from app.telegram.templates import (
    TEMPLATES,
    MissingTemplateData,
    UnknownTemplate,
    render,
)


def test_render_help_lists_every_command() -> None:
    text = render("help")
    for command in COMMANDS:
        if command != "start":
            assert f"/{command}:" in text


def test_values_are_escaped() -> None:
    text = render("unknown_command", {"command": "<b>&"})
    assert "&lt;b&gt;&amp;" in text
    assert "<b>&" not in text


def test_template_markup_is_not_escaped() -> None:
    assert render("unknown_command", {"command": "x"}).startswith(
        "I don't know <code>/x</code>."
    )
    assert render("help").startswith("<b>What I can do</b>")


def test_braces_in_values_are_not_reformatted() -> None:
    assert "<code>/{command}</code>" in render("unknown_command", {"command": "{command}"})


def test_unknown_template_raises() -> None:
    with pytest.raises(UnknownTemplate):
        render("nope")


def test_missing_field_raises_with_field_name() -> None:
    with pytest.raises(MissingTemplateData) as caught:
        render("unknown_command")
    assert caught.value.field == "command"
    assert caught.value.template == "unknown_command"


def test_unknown_language_falls_back_to_english() -> None:
    assert render("working", lang="xx") == render("working") == "Working on it…"


def test_overlong_result_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(templates, "TEMPLATES", {"echo": {"en": "{value}"}})
    assert render("echo", {"value": "x" * 4096}) == "x" * 4096
    with pytest.raises(ValueError):
        render("echo", {"value": "x" * 4097})
    # Escaping counts: 1366 '&' become 6830 characters.
    with pytest.raises(ValueError):
        render("echo", {"value": "&" * 1366})


def test_every_handler_template_exists() -> None:
    names = {
        asyncio.run(handler(None, None, None)).template  # type: ignore[arg-type]
        for handler in (*HANDLERS.values(), not_available)
    }
    assert names <= TEMPLATES.keys()


def test_table_is_immutable() -> None:
    with pytest.raises(TypeError):
        TEMPLATES["new"] = {"en": "x"}  # type: ignore[index]
    with pytest.raises(TypeError):
        TEMPLATES["help"]["en"] = "x"  # type: ignore[index]
