"""Tests for POST /integrations/telegram/webhook (BE-008).

The route is public: no API key, guarded by the Telegram secret header.
Every recorded fixture is accepted with `200 {"ok": true}` and nothing else
happens yet.
"""

import pytest
from fastapi.testclient import TestClient

from app.telegram.security import TELEGRAM_SECRET_HEADER
from tests.conftest import KEY_ONE
from tests.telegram_fixtures import FIXTURE_NAMES, load_payload

WEBHOOK = "/integrations/telegram/webhook"
SECRET = "test-webhook-secret_0123456789"


@pytest.fixture()
def webhook_client(make_client, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", SECRET)
    return make_client(KEY_ONE)


def _secret() -> dict[str, str]:
    return {TELEGRAM_SECRET_HEADER: SECRET}


def test_webhook_without_secret_is_401(webhook_client: TestClient) -> None:
    assert webhook_client.post(WEBHOOK, json={}).status_code == 401


def test_webhook_with_wrong_secret_is_401(webhook_client: TestClient) -> None:
    response = webhook_client.post(
        WEBHOOK, json={}, headers={TELEGRAM_SECRET_HEADER: "wrong-secret_0123456789"}
    )
    assert response.status_code == 401


def test_webhook_with_api_key_but_no_secret_is_401(webhook_client: TestClient) -> None:
    # A valid API key alone does not open the webhook.
    response = webhook_client.post(WEBHOOK, json={}, headers={"X-API-Key": KEY_ONE})
    assert response.status_code == 401


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_webhook_accepts_each_fixture(webhook_client: TestClient, name: str) -> None:
    response = webhook_client.post(WEBHOOK, json=load_payload(name), headers=_secret())
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_unparseable_update_is_still_200(webhook_client: TestClient) -> None:
    response = webhook_client.post(WEBHOOK, json={"foo": 1}, headers=_secret())
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_webhook_is_not_in_openapi(webhook_client: TestClient) -> None:
    response = webhook_client.get("/openapi.json")
    assert response.status_code == 200
    assert WEBHOOK not in response.text
