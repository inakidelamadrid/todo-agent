"""Loaders for the recorded Telegram update fixtures (BE-005).

A loader and nothing else: fixture JSON on disk -> aiogram's typed
``Update`` model. All fixture data is synthetic (user/chat IDs are
``111111``, ``999999`` and ``222222`` only).
"""

import json
from pathlib import Path
from typing import Any

from aiogram.types import Update

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "telegram"

FIXTURE_NAMES = (
    "text",
    "command",
    "voice",
    "photo",
    "document",
    "callback_query",
    "stranger_text",
)


def load_payload(name: str) -> dict[str, Any]:
    """Return the raw JSON payload for a fixture named without extension."""
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text())


def load_update(name: str) -> Update:
    """Return the fixture parsed into aiogram's typed ``Update`` model."""
    return Update.model_validate(load_payload(name))
