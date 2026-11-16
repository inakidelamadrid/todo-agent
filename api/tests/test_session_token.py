"""Tests for the session-token port, verify_session and the fake decoder."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.principal import ClerkRules, Rejected, User
from app.session_token import DecodeToken, get_token_decoder, verify_session
from app.settings import Settings
from tests.fakes import fake_decoder, make_claims

NOW = 1_800_000_000
RULES = ClerkRules(
    authorized_parties=("http://localhost:5173",),
    allowed_user_ids=("user_owner",),
)
TOKEN = "fake-token-string"


def test_verify_session_returns_user_for_a_known_good_token() -> None:
    result = verify_session(TOKEN, fake_decoder({TOKEN: make_claims()}), RULES, NOW)
    assert result == User(user_id="user_owner")


def test_verify_session_unknown_token_is_malformed() -> None:
    result = verify_session("no-such-token", fake_decoder({}), RULES, NOW)
    assert result == Rejected("malformed")


def test_verify_session_passes_claim_rejections_through() -> None:
    expired = fake_decoder({TOKEN: make_claims(exp=NOW - 100)})
    assert verify_session(TOKEN, expired, RULES, NOW) == Rejected("expired")

    stranger = fake_decoder({TOKEN: make_claims(sub="user_nope")})
    assert verify_session(TOKEN, stranger, RULES, NOW) == Rejected("not_owner")

    wrong_origin = fake_decoder({TOKEN: make_claims(azp="https://evil.example")})
    assert verify_session(TOKEN, wrong_origin, RULES, NOW) == Rejected("wrong_party")


def test_default_decoder_rejects_everything() -> None:
    # Calling the dependency body directly: its default adapter fails closed.
    decode = get_token_decoder(Settings(_env_file=None, api_keys="k"))
    for token in ("anything", "", "garbled", TOKEN):
        assert decode(token) is None


def test_decoder_dependency_can_be_overridden() -> None:
    app = FastAPI()

    @app.get("/probe")
    def probe(decode: Annotated[DecodeToken, Depends(get_token_decoder)]) -> dict:
        return {"result": decode("probe-token")}

    fake = fake_decoder({"probe-token": make_claims()})
    app.dependency_overrides[get_token_decoder] = lambda: fake

    response = TestClient(app).get("/probe")
    assert response.status_code == 200
    assert response.json()["result"]["sub"] == "user_owner"


def test_fake_decoder_yields_none_for_unknown() -> None:
    decode = fake_decoder({TOKEN: make_claims()})
    assert decode(TOKEN) is not None
    assert decode("other") is None


def test_make_claims_overrides() -> None:
    assert make_claims()["exp"] > NOW
    assert make_claims(sub="x")["sub"] == "x"
