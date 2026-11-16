"""Tests for require_principal (BE-062) through a throwaway FastAPI app.

Clock, decoder and settings are pinned via dependency_overrides; tokens come
from tests/fakes.py — no real key pair anywhere.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.principal import Machine, User
from app.security import get_now, require_principal
from app.session_token import get_token_decoder
from app.settings import Settings, get_settings
from tests.fakes import fake_decoder, make_claims

NOW = 1_800_000_000
API_KEY = "machine-key"
TOKEN = "owner-token"
BAD_TOKEN = "bad-token"

ORIGIN = "http://localhost:5173"
OWNER = "user_owner"

CLAIMS = make_claims()  # sub=user_owner, azp=ORIGIN, exp far future


def _settings(**overrides: str) -> Settings:
    base = {
        "api_keys": API_KEY,
        "clerk_authorized_parties": ORIGIN,
        "clerk_allowed_user_ids": OWNER,
    }
    return Settings(_env_file=None, **{**base, **overrides})


def _app(claims_table=None) -> TestClient:
    app = FastAPI()

    @app.get("/probe")
    def probe(principal=Depends(require_principal)):
        body = {"kind": type(principal).__name__}
        if isinstance(principal, User):
            body["userId"] = principal.user_id
        if isinstance(principal, Machine):
            body["keyLabel"] = principal.key_label
        return body

    table = {TOKEN: CLAIMS, **(claims_table or {})}
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_token_decoder] = lambda: fake_decoder(table)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    return _app()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_no_credentials_returns_401_with_both_challenges(client: TestClient) -> None:
    response = client.get("/probe")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"
    assert response.json() == {"detail": "Invalid or missing credentials"}


def test_wrong_api_key_returns_401(client: TestClient) -> None:
    assert client.get("/probe", headers={"X-API-Key": "wrong"}).status_code == 401


def test_valid_api_key_returns_machine(client: TestClient) -> None:
    response = client.get("/probe", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    assert response.json() == {"kind": "Machine", "keyLabel": "api-key"}


def test_valid_owner_token_returns_user(client: TestClient) -> None:
    response = client.get("/probe", headers=bearer(TOKEN))
    assert response.status_code == 200
    assert response.json() == {"kind": "User", "userId": OWNER}


def test_expired_token_returns_401() -> None:
    client = _app({TOKEN: make_claims(exp=NOW - 100)})
    response = client.get("/probe", headers=bearer(TOKEN))
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"


def test_token_for_another_origin_returns_401() -> None:
    client = _app({TOKEN: make_claims(azp="https://evil.example")})
    assert client.get("/probe", headers=bearer(TOKEN)).status_code == 401


def test_malformed_token_returns_401(client: TestClient) -> None:
    assert client.get("/probe", headers=bearer(BAD_TOKEN)).status_code == 401
    # Also malformed by claim shape, not just unknown signature.
    client = _app({TOKEN: make_claims(exp="not-an-int")})
    assert client.get("/probe", headers=bearer(TOKEN)).status_code == 401


def test_token_for_non_owner_returns_403() -> None:
    client = _app({TOKEN: make_claims(sub="user_other")})
    response = client.get("/probe", headers=bearer(TOKEN))
    assert response.status_code == 403
    assert response.json() == {"detail": "Not allowed"}
    assert "WWW-Authenticate" not in response.headers


def test_bad_bearer_is_not_rescued_by_valid_api_key(client: TestClient) -> None:
    response = client.get(
        "/probe", headers={**bearer(BAD_TOKEN), "X-API-Key": API_KEY}
    )
    assert response.status_code == 401


def test_valid_bearer_wins_over_wrong_api_key(client: TestClient) -> None:
    response = client.get(
        "/probe", headers={**bearer(TOKEN), "X-API-Key": "wrong"}
    )
    assert response.status_code == 200
    assert response.json()["kind"] == "User"


def test_other_authorization_scheme_is_ignored(client: TestClient) -> None:
    response = client.get(
        "/probe", headers={"Authorization": "Basic abc", "X-API-Key": API_KEY}
    )
    assert response.status_code == 200
    assert response.json()["kind"] == "Machine"


def test_responses_never_echo_credentials(client: TestClient) -> None:
    cases = [
        client.get("/probe", headers=bearer(TOKEN)),
        client.get("/probe", headers=bearer(BAD_TOKEN)),
        client.get("/probe", headers={"X-API-Key": API_KEY}),
        client.get("/probe", headers={"X-API-Key": "wrong"}),
        client.get("/probe"),
    ]
    for response in cases:
        leaked = response.text + " " + " ".join(response.headers.values())
        assert TOKEN not in leaked
        assert API_KEY not in leaked
        assert BAD_TOKEN not in leaked
