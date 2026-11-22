"""Tests for require_telegram_secret (BE-007) via a throwaway probe app."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.settings import Settings, get_settings
from app.telegram.security import DETAIL_INVALID_SECRET, TELEGRAM_SECRET_HEADER, require_telegram_secret

SECRET = "test-webhook-secret_0123456789"
PROBE = "/probe"


def _app(secret: str = SECRET) -> TestClient:
    settings = Settings(
        _env_file=None, api_keys="k", telegram_webhook_secret=secret
    )
    app = FastAPI()

    @app.get(PROBE, dependencies=[Depends(require_telegram_secret)])
    def probe() -> dict[str, bool]:
        return {"ok": True}

    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def header(value: str) -> dict[str, str]:
    return {TELEGRAM_SECRET_HEADER: value}


def test_missing_header_is_401() -> None:
    response = _app().get(PROBE)
    assert response.status_code == 401
    assert response.json() == {"detail": DETAIL_INVALID_SECRET}


def test_wrong_secret_is_401() -> None:
    assert _app().get(PROBE, headers=header("wrong-secret_0123456789")).status_code == 401


def test_correct_secret_passes() -> None:
    response = _app().get(PROBE, headers=header(SECRET))
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_unconfigured_secret_rejects_everything() -> None:
    app = _app(secret="")
    assert app.get(PROBE).status_code == 401
    assert app.get(PROBE, headers=header("")).status_code == 401


def test_error_body_does_not_contain_the_secret() -> None:
    app = _app()
    attempts = [
        (app.get(PROBE), SECRET),
        (app.get(PROBE, headers=header("wrong-secret_0123456789")), "wrong-secret_0123456789"),
        (app.get(PROBE, headers=header(SECRET[:5])), SECRET),
    ]
    for response, value in attempts:
        leaked = response.text + " " + " ".join(response.headers.values())
        assert value not in leaked
