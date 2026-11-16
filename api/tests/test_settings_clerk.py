"""Settings for Clerk user login (BE-058): pure parsers, fail-closed check.

All constructions use ``_env_file=None`` so tests never read the developer's
real ``api/.env``.
"""

import pytest

from app.settings import Settings, clerk_enabled, normalize_pem, parse_csv


def _settings(**overrides):
    base = {"api_keys": "test"}
    return Settings(_env_file=None, **{**base, **overrides})


def test_parse_csv_splits_trims_and_drops_empties() -> None:
    assert parse_csv(" a , ,b,") == ("a", "b")
    assert parse_csv("") == ()
    assert parse_csv(",, ,") == ()


def test_normalize_pem_turns_escaped_newlines_into_real_ones() -> None:
    assert normalize_pem("-----BEGIN X-----\\nabc\\n-----END X-----") == (
        "-----BEGIN X-----\nabc\n-----END X-----"
    )
    # An already multi-line value is unchanged apart from trimming.
    multi = "  -----BEGIN X-----\nabc\n-----END X-----\n"
    assert normalize_pem(multi) == multi.strip()
    assert normalize_pem("") == ""


@pytest.mark.parametrize(
    "missing",
    ["clerk_jwt_public_key", "clerk_authorized_parties", "clerk_allowed_user_ids"],
)
def test_clerk_enabled_false_when_any_value_is_missing(missing: str) -> None:
    values = {
        "clerk_jwt_public_key": "-----BEGIN PUBLIC KEY-----\\nyz\\n-----END PUBLIC KEY-----",
        "clerk_authorized_parties": "http://localhost:5173",
        "clerk_allowed_user_ids": "user_2abc",
    }
    assert clerk_enabled(Settings(_env_file=None, **{**values, missing: ""})) is False
    # The two CSV values are also missing when they contain only separators.
    if missing != "clerk_jwt_public_key":
        assert (
            clerk_enabled(Settings(_env_file=None, **{**values, missing: " , ,"}))
            is False
        )


def test_clerk_enabled_true_when_all_three_are_set() -> None:
    settings = _settings(
        clerk_jwt_public_key="-----BEGIN PUBLIC KEY-----\\nyz\\n-----END PUBLIC KEY-----",
        clerk_authorized_parties="http://localhost:5173, http://127.0.0.1:5173",
        clerk_allowed_user_ids="user_2abc",
    )
    assert clerk_enabled(settings) is True


def test_settings_still_start_without_clerk_values() -> None:
    settings = _settings()
    assert settings.clerk_jwt_public_key == ""
    assert settings.clerk_authorized_parties == ""
    assert settings.clerk_allowed_user_ids == ""
    assert clerk_enabled(settings) is False
