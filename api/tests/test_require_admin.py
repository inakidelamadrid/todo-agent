"""Tests for require_admin (BE-066) through a throwaway FastAPI app.

Decoder and settings are pinned via dependency_overrides; tokens come from
tests/fakes.py. The function reads no header itself: every 401 comes from
require_principal upstream.
"""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security import get_now, require_admin
from app.session_token import get_token_decoder
from app.settings import Settings, get_settings
from tests.fakes import fake_decoder, make_claims

NOW = 1_800_000_000
API_KEY = "machine-key"
ADMIN_TOKEN = "admin-token"
OTHER_TOKEN = "other-token"

ORIGIN = "http://localhost:5173"
ADMIN = "user_owner"
OTHER = "user_other"

TOKENS = {
    ADMIN_TOKEN: make_claims(sub=ADMIN),
    OTHER_TOKEN: make_claims(sub=OTHER),
}


def _settings(**overrides: str) -> Settings:
    base = {
        "api_keys": API_KEY,
        "clerk_authorized_parties": ORIGIN,
        "clerk_allowed_user_ids": f"{ADMIN},{OTHER}",
        "admin_user_ids": ADMIN,
    }
    return Settings(_env_file=None, **{**base, **overrides})


def _app(**overrides: str) -> TestClient:
    app = FastAPI()

    @app.get("/probe")
    def probe(user=Depends(require_admin)):
        return {"kind": type(user).__name__, "userId": user.user_id}

    app.dependency_overrides[get_settings] = lambda: _settings(**overrides)
    app.dependency_overrides[get_token_decoder] = lambda: fake_decoder(TOKENS)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_user_passes_and_gets_user_object() -> None:
    response = _app().get("/probe", headers=bearer(ADMIN_TOKEN))
    assert response.status_code == 200
    assert response.json() == {"kind": "User", "userId": ADMIN}


def test_non_admin_user_gets_403() -> None:
    response = _app().get("/probe", headers=bearer(OTHER_TOKEN))
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access is required"}


def test_machine_gets_403() -> None:
    response = _app().get("/probe", headers={"X-API-Key": API_KEY})
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access is required"}


def test_no_credentials_gets_401() -> None:
    response = _app().get("/probe")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"


def test_wrong_api_key_gets_401() -> None:
    response = _app().get("/probe", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"


def test_empty_admin_list_denies_everyone() -> None:
    response = _app(admin_user_ids="").get("/probe", headers=bearer(ADMIN_TOKEN))
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access is required"}
