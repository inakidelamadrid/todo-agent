"""Playground switch and guarded /admin/telegram router (BE-068).

Probe route GET /admin/telegram/playground proves the guard order:
require_admin (401/403) before require_playground (404 when off).
"""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings, get_settings, playground_allowed
from tests.conftest import KEY_ONE, OWNER_USER_ID, sign_token

OTHER_USER_ID = "user_other"
PROBE = "/admin/telegram/playground"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def playground_client(
    make_client: Callable[[str], TestClient], monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Real app, switch on: OWNER is admin, OTHER is signed-in but not."""
    monkeypatch.setenv("TELEGRAM_PLAYGROUND_ENABLED", "true")
    monkeypatch.setenv("ADMIN_USER_IDS", OWNER_USER_ID)
    monkeypatch.setenv("CLERK_ALLOWED_USER_IDS", f"{OWNER_USER_ID},{OTHER_USER_ID}")
    return make_client(KEY_ONE)


@pytest.fixture()
def playground_off_client(
    make_client: Callable[[str], TestClient], monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Real app, switch off (the default), OWNER still admin."""
    monkeypatch.setenv("ADMIN_USER_IDS", OWNER_USER_ID)
    return make_client(KEY_ONE)


def test_probe_without_credentials_returns_401(playground_client: TestClient) -> None:
    response = playground_client.get(PROBE)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"


def test_probe_as_non_admin_returns_403(playground_client: TestClient) -> None:
    response = playground_client.get(PROBE, headers=bearer(sign_token(sub=OTHER_USER_ID)))
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access is required"}


def test_probe_as_machine_returns_403(playground_client: TestClient) -> None:
    response = playground_client.get(PROBE, headers={"X-API-Key": KEY_ONE})
    assert response.status_code == 403


def test_probe_when_playground_off_returns_404(
    playground_off_client: TestClient,
) -> None:
    response = playground_off_client.get(PROBE, headers=bearer(sign_token()))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_probe_as_admin_returns_enabled_true(playground_client: TestClient) -> None:
    response = playground_client.get(PROBE, headers=bearer(sign_token()))
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


def test_openapi_schema_hides_the_playground(
    playground_off_client: TestClient, playground_client: TestClient
) -> None:
    # The schema reveals nothing in any environment: no /admin/telegram path,
    # whether the switch is off or on.
    for app_client in (playground_off_client, playground_client):
        response = app_client.get("/openapi.json")
        assert response.status_code == 200
        assert "/admin/telegram" not in response.text


def test_app_refuses_to_start_with_playground_on_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TELEGRAM_PLAYGROUND_ENABLED", "true")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="APP_ENV"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_playground_allowed_truth_table() -> None:
    def _settings(env: str, switch: bool) -> Settings:
        return Settings(
            _env_file=None,
            api_keys="k",
            app_env=env,  # type: ignore[arg-type]
            telegram_playground_enabled=switch,
        )

    assert playground_allowed(_settings("development", True)) is True
    assert playground_allowed(_settings("development", False)) is False
    assert playground_allowed(_settings("production", True)) is False
    assert playground_allowed(_settings("production", False)) is False
