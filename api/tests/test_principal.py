"""Table-style tests for the pure claim checks (BE-059)."""

import pytest
from dataclasses import FrozenInstanceError

from app.principal import (
    LEEWAY_SECONDS,
    ClerkRules,
    Machine,
    Rejected,
    User,
    check_claims,
)

NOW = 1_800_000_000
RULES = ClerkRules(
    authorized_parties=("http://localhost:5173",),
    allowed_user_ids=("user_1",),
)
VALID = {
    "sub": "user_1",
    "exp": NOW + 60,
    "azp": "http://localhost:5173",
}


def _check(**overrides):
    claims = {**VALID, **overrides}
    return check_claims({k: v for k, v in claims.items() if v is not None}, RULES, NOW)


def test_valid_claims_return_user() -> None:
    assert check_claims(VALID, RULES, NOW) == User(user_id="user_1")


@pytest.mark.parametrize("sub", [None, "", "   ", 42, ["user_1"]])
def test_missing_or_blank_sub_is_malformed(sub) -> None:
    assert _check(sub=sub) == Rejected("malformed")


@pytest.mark.parametrize("exp", [None, "123", 1.5, True, False])
def test_missing_or_bad_typed_exp_is_malformed(exp) -> None:
    # covers test_missing_exp / test_exp_as_string / test_bool_exp
    assert _check(exp=exp) == Rejected("malformed")


@pytest.mark.parametrize("azp", [None, "", "   ", 42])
def test_missing_azp_is_malformed(azp) -> None:
    assert _check(azp=azp) == Rejected("malformed")


@pytest.mark.parametrize("nbf", ["123", 1.5, True])
def test_bad_typed_nbf_is_malformed(nbf) -> None:
    assert _check(nbf=nbf) == Rejected("malformed")


def test_expired_token_is_rejected() -> None:
    # Boundary: expired exactly when exp + LEEWAY <= now.
    assert _check(exp=NOW - LEEWAY_SECONDS) == Rejected("expired")
    assert _check(exp=NOW - LEEWAY_SECONDS - 1) == Rejected("expired")


def test_token_inside_leeway_is_still_valid() -> None:
    assert _check(exp=NOW - LEEWAY_SECONDS + 1) == User(user_id="user_1")
    assert _check(exp=NOW - 1) == User(user_id="user_1")


def test_nbf_in_the_future_is_not_yet_valid() -> None:
    # Boundary: not yet valid exactly when nbf - LEEWAY > now.
    assert _check(nbf=NOW + LEEWAY_SECONDS + 1) == Rejected("not_yet_valid")
    assert _check(nbf=NOW + LEEWAY_SECONDS) == User(user_id="user_1")


def test_missing_nbf_is_fine() -> None:
    assert _check() == User(user_id="user_1")


def test_azp_not_listed_is_wrong_party() -> None:
    assert _check(azp="https://evil.example") == Rejected("wrong_party")


def test_sub_not_listed_is_not_owner() -> None:
    assert _check(sub="user_2") == Rejected("not_owner")


def test_empty_rules_reject_everyone() -> None:
    # With empty rules, even the right-looking origin and owner fail.
    assert check_claims(VALID, ClerkRules((), ()), NOW) == Rejected("wrong_party")
    assert check_claims(VALID, ClerkRules((), ("user_1",)), NOW) == Rejected("wrong_party")
    assert (
        check_claims(VALID, ClerkRules(("http://localhost:5173",), ()), NOW)
        == Rejected("not_owner")
    )


def test_check_order_expired_beats_wrong_party() -> None:
    claims = {**VALID, "exp": NOW - 100, "azp": "https://evil.example", "sub": "user_2"}
    assert check_claims(claims, RULES, NOW) == Rejected("expired")
    # And a malformed-but-also-expired token reports malformed first.
    claims = {**VALID, "exp": "not-an-int", "azp": "https://evil.example"}
    assert check_claims(claims, RULES, NOW) == Rejected("malformed")


def test_check_returns_values_never_raises() -> None:
    assert check_claims({}, RULES, NOW) == Rejected("malformed")


def test_principal_types_are_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        User(user_id="user_1").user_id = "user_2"
    with pytest.raises(FrozenInstanceError):
        Machine(key_label="a").key_label = "b"
    with pytest.raises(FrozenInstanceError):
        Rejected(reason="expired").reason = "malformed"
    with pytest.raises(FrozenInstanceError):
        RULES.allowed_user_ids = ()  # type: ignore[misc]
