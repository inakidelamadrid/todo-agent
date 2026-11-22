"""Message templates with central HTML escaping (BE-020).

``render`` is the only place message text is assembled. Template text is
trusted HTML (Telegram's subset); every data value is untrusted and passes
through ``html.escape`` here, so no feature can forget it. Pure: no I/O, no
aiogram.

Each feature epic adds its own rows to ``TEMPLATES``. The language level is
there so Spanish can be added without changing callers.
"""

import html
from collections.abc import Mapping
from types import MappingProxyType

DEFAULT_LANG = "en"
MESSAGE_TEXT_MAX_CHARS = 4096  # Telegram's limit

_HELP_EN = "\n".join(
    [
        "<b>What I can do</b>",
        "",
        "/now: what to do now",
        "/inbox: inbox count and link",
        "/done: finish the current focus task",
        "/today: today's spending",
        "/month: this month's spending",
        "/radar: what's coming up",
        "/reset: start the weekly reset",
        "/vault: send the next photo or PDF to the vault",
        "/undo: undo the last action",
        "/pause: pause notifications",
        "/resume: resume notifications",
        "/help: this list",
    ]
)

TEMPLATES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "help": MappingProxyType({"en": _HELP_EN}),
        "not_available": MappingProxyType({"en": "That isn't available yet."}),
        "unknown_command": MappingProxyType(
            {"en": "I don't know <code>/{command}</code>. Try /help."}
        ),
        "unsupported": MappingProxyType({"en": "I can't read that kind of message yet."}),
        "working": MappingProxyType({"en": "Working on it…"}),
        "expired_button": MappingProxyType({"en": "That button has expired."}),
    }
)


class UnknownTemplate(KeyError):
    def __init__(self, template: str) -> None:
        super().__init__(template)
        self.template = template


class MissingTemplateData(KeyError):
    def __init__(self, template: str, field: str) -> None:
        super().__init__(f"{template}: missing {field}")
        self.template = template
        self.field = field


def render(template: str, data: Mapping[str, str] | None = None, lang: str = DEFAULT_LANG) -> str:
    """The final message text: ``template`` in ``lang`` (falling back to
    English) filled with HTML-escaped ``data``."""
    texts = TEMPLATES.get(template)
    if texts is None:
        raise UnknownTemplate(template)
    text = texts.get(lang, texts[DEFAULT_LANG])
    escaped = {key: html.escape(value, quote=False) for key, value in (data or {}).items()}
    try:
        result = text.format_map(escaped)
    except KeyError as missing:
        raise MissingTemplateData(template, str(missing.args[0])) from None
    if len(result) > MESSAGE_TEXT_MAX_CHARS:
        raise ValueError(f"{template}: rendered text exceeds {MESSAGE_TEXT_MAX_CHARS} characters")
    return result
