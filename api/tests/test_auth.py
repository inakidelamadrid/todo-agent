"""API key authentication: protected by default, fail-fast without keys."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.settings import Settings, get_settings
from tests.conftest import KEY_ONE, KEY_TWO, PROTECTED_PROBE_PATH


def test_protected_route_without_key_returns_401(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}
    assert response.headers["WWW-Authenticate"] == "ApiKey"


def test_protected_route_with_wrong_key_returns_401(client: TestClient) -> None:
    response = client.get(PROTECTED_PROBE_PATH, headers={"X-API-Key": "not-a-real-key"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}
    assert response.headers["WWW-Authenticate"] == "ApiKey"


def test_protected_route_with_valid_key_returns_200(client: TestClient) -> None:
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


@pytest.mark.parametrize("raw_keys", ["", "   ", " , ,"])
def test_settings_reject_missing_or_empty_api_keys(
    monkeypatch: pytest.MonkeyPatch, tmp_path, raw_keys: str
) -> None:
    # chdir removes any developer .env from the equation; env var overrides it.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("API_KEYS", raising=False)
    if raw_keys:
        monkeypatch.setenv("API_KEYS", raw_keys)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_app_refuses_to_start_without_api_keys(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)  # ensure no local .env supplies keys
    monkeypatch.delenv("API_KEYS", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError):
            create_app()
    finally:
        get_settings.cache_clear()


def test_openapi_documents_api_key_scheme(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()

    schemes = spec["components"]["securitySchemes"]
    assert any(
        scheme.get("type") == "apiKey"
        and scheme.get("in") == "header"
        and scheme.get("name") == "X-API-Key"
        for scheme in schemes.values()
    )


def test_openapi_shows_scheme_even_without_protected_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEYS", KEY_ONE)
    get_settings.cache_clear()
    try:
        bare_client = TestClient(create_app())  # no protected router mounted
        schemes = bare_client.get("/openapi.json").json()["components"]["securitySchemes"]
        assert any(
            scheme.get("type") == "apiKey" and scheme.get("name") == "X-API-Key"
            for scheme in schemes.values()
        )
    finally:
        get_settings.cache_clear()


def test_openapi_marks_protected_route_as_secured(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()

    assert spec["paths"][PROTECTED_PROBE_PATH]["get"]["security"]
    assert spec["paths"]["/health"]["get"].get("security") in (None, [])
    assert spec["paths"]["/ping"]["get"].get("security") in (None, [])
