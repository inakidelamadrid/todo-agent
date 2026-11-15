"""The recorded Telegram fixtures parse into aiogram's typed Update model."""

import pytest

from tests.telegram_fixtures import FIXTURE_NAMES, load_payload, load_update

SYNTHETIC_USER_IDS = {111111, 999999}


def _payload_field(payload: dict) -> dict:
    """The single payload object of an update: ``message`` or ``callback_query``."""
    return next(v for k, v in payload.items() if k != "update_id" and v)


def _user_id(field: dict) -> int:
    sender = field.get("from")
    assert isinstance(sender, dict), "fixture field must have a sender"
    return sender["id"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_every_fixture_parses(name: str) -> None:
    update = load_update(name)
    assert isinstance(update.update_id, int)


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixtures_use_only_synthetic_ids(name: str) -> None:
    assert _user_id(_payload_field(load_payload(name))) in SYNTHETIC_USER_IDS


def test_update_ids_are_unique_across_fixtures() -> None:
    assert len(FIXTURE_NAMES) == 7
    ids = [load_payload(name)["update_id"] for name in FIXTURE_NAMES]
    assert len(set(ids)) == len(ids)
