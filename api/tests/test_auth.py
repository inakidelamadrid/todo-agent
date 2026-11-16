"""Authentication: protected by default, people and machines both in.

Missing/wrong credentials get 401 with both challenges; a session token from
someone who is not the owner gets 403; public routes stay open.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.settings import Settings, get_settings
from tests.conftest import KEY_ONE, KEY_TWO, PROTECTED_PROBE_PATH, sign_token

INVALID = "Invalid or missing credentials"
BOTH_CHALLENGES = "Bearer, ApiKey"


def test_protected_route_without_credentials_returns_401(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH)

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID}
    assert response.headers["WWW-Authenticate"] == BOTH_CHALLENGES


def test_protected_route_with_wrong_key_returns_401(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH, headers={"X-API-Key": "not-a-real-key"})

    assert response.status_code == 401
    assert response.json() == {"detail": INVALID}
    assert response.headers["WWW-Authenticate"] == BOTH_CHALLENGES


def test_protected_route_with_valid_key_still_works(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH, headers={"X-API-Key": KEY_ONE})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_all_configured_keys_work(client: TestClient) -> None:
    for key in (KEY_ONE, KEY_TWO):
        response = client.get(PROTECTED_PROBE_PATH, headers={"X-API-Key": key})
        assert response.status_code == 200


def test_rejected_key_is_never_echoed(client: TestClient) -> None:
    attempted = "super-secret-attempt"
    response = client.get(PROTECTED_PROBE_PATH, headers={"X-API-Key": attempted})

    assert attempted not in response.text


# --- BE-063: the app is unusable until Clerk is fully configured -----------


@pytest.mark.parametrize(
    "missing",
    ["CLERK_JWT_PUBLIC_KEY", "CLERK_AUTHORIZED_PARTIES", "CLERK_ALLOWED_USER_IDS"],
)
def test_app_refuses_to_start_without_clerk_values(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    secret_value = "hunter2-not-echoed"
    monkeypatch.setenv(missing, "")
    if missing != "CLERK_JWT_PUBLIC_KEY":
        monkeypatch.setenv("CLERK_JWT_PUBLIC_KEY", secret_value)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError) as exc_info:
            create_app()
        assert "must all be set" in str(exc_info.value)
        assert secret_value not in str(exc_info.value)  # never echoes a value
    finally:
        get_settings.cache_clear()


# --- BE-063: people on the protected routes (real RS256, test key pair) -----


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_protected_route_with_owner_token_works(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH, headers=bearer(sign_token()))
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_protected_route_with_other_user_token_returns_403(client: TestClient) -> None:
    response = client.get(
        PROTECTED_PROBE_PATH, headers=bearer(sign_token(sub="user_stranger"))
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not allowed"}


def test_protected_route_with_expired_token_returns_401(client: TestClient) -> None:
    import time

    expired = sign_token(exp=int(time.time()) - 3600)
    response = client.get(PROTECTED_PROBE_PATH, headers=bearer(expired))
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == BOTH_CHALLENGES


def test_protected_route_with_other_origin_token_returns_401(
    client: TestClient,
) -> None:
    response = client.get(
        PROTECTED_PROBE_PATH, headers=bearer(sign_token(azp="https://evil.example"))
    )
    assert response.status_code == 401


def test_public_routes_stay_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/ping").status_code == 200


def test_openapi_lists_both_security_schemes(client: TestClient) -> None:
    schemes = client.get("/openapi.json").json()["components"]["securitySchemes"]
    assert schemes["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    assert schemes["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }


@pytest.mark.parametrize("raw_keys", ["", "   ", " , ,"])
def test_settings_reject_missing_or_empty_api_keys(
    monkeypatch: pytest.MonkeyPatch, raw_keys: str
) -> None:
    monkeypatch.delenv("API_KEYS", raising=False)
    if raw_keys:
        monkeypatch.setenv("API_KEYS", raw_keys)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
