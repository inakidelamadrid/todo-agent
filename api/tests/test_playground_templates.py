"""Playground template list and preview (BE-078)."""

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.main import create_app
from app.settings import Settings, get_settings
from app.telegram.playground.models import PlaygroundAction
from app.telegram.templates import TEMPLATES
from tests.conftest import KEY_ONE, OWNER_USER_ID, _admin_exec, sign_token

OTHER_USER_ID = "user_other"
TEMPLATES_URL = "/admin/telegram/templates"
PREVIEW_URL = "/admin/telegram/templates/preview"
BODY = {"template": "unknown_command", "data": {"command": "<b>x</b>"}}


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


ADMIN = bearer(sign_token())


def _client(monkeypatch: pytest.MonkeyPatch, db: str, playground: bool) -> Iterator[TestClient]:
    monkeypatch.setenv("API_KEYS", KEY_ONE)
    monkeypatch.setenv("POSTGRES_DB", db)
    monkeypatch.setenv("TELEGRAM_PLAYGROUND_ENABLED", str(playground).lower())
    monkeypatch.setenv("ADMIN_USER_IDS", OWNER_USER_ID)
    monkeypatch.setenv("CLERK_ALLOWED_USER_IDS", f"{OWNER_USER_ID},{OTHER_USER_ID}")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            yield client
    finally:
        get_settings.cache_clear()


@pytest.fixture()
def clean_actions(migrated_test_db: str) -> Iterator[None]:
    """Empty before and after: previews commit their rows, and other tests on
    this worker (test_playground_actions) expect the table to start empty."""
    settings = Settings(api_keys="test-suite")
    asyncio.run(_admin_exec(settings, "DELETE FROM playground_actions", migrated_test_db))
    yield
    asyncio.run(_admin_exec(settings, "DELETE FROM playground_actions", migrated_test_db))


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch, migrated_test_db: str, clean_actions: None
) -> Iterator[TestClient]:
    yield from _client(monkeypatch, migrated_test_db, playground=True)


@pytest.fixture()
def off_client(
    monkeypatch: pytest.MonkeyPatch, migrated_test_db: str, clean_actions: None
) -> Iterator[TestClient]:
    yield from _client(monkeypatch, migrated_test_db, playground=False)


def _outcomes(db: str) -> list[str]:
    async def read() -> list[str]:
        engine = create_async_engine(Settings(api_keys="test-suite", postgres_db=db).database_url)
        try:
            async with AsyncSession(engine) as session:
                rows = await session.scalars(
                    select(PlaygroundAction.outcome)
                    .where(PlaygroundAction.tool == "template_preview")
                    .order_by(PlaygroundAction.created_at)
                )
                return list(rows)
        finally:
            await engine.dispose()

    return asyncio.run(read())


def _get(client: TestClient, headers: dict[str, str] | None = None) -> int:
    return client.get(TEMPLATES_URL, headers=headers or {}).status_code


def _post(client: TestClient, headers: dict[str, str] | None = None) -> int:
    return client.post(PREVIEW_URL, json=BODY, headers=headers or {}).status_code


# --- Guards, both routes ----------------------------------------------------


def test_templates_without_credentials_returns_401(client: TestClient) -> None:
    assert _get(client) == 401


def test_templates_as_non_admin_returns_403(client: TestClient) -> None:
    assert _get(client, bearer(sign_token(sub=OTHER_USER_ID))) == 403


def test_templates_as_machine_returns_403(client: TestClient) -> None:
    assert _get(client, {"X-API-Key": KEY_ONE}) == 403


def test_templates_when_playground_off_returns_404(off_client: TestClient) -> None:
    assert _get(off_client, ADMIN) == 404


def test_preview_without_credentials_returns_401(client: TestClient) -> None:
    assert _post(client) == 401


def test_preview_as_non_admin_returns_403(client: TestClient) -> None:
    assert _post(client, bearer(sign_token(sub=OTHER_USER_ID))) == 403


def test_preview_as_machine_returns_403(client: TestClient) -> None:
    assert _post(client, {"X-API-Key": KEY_ONE}) == 403


def test_preview_when_playground_off_returns_404(off_client: TestClient) -> None:
    assert _post(off_client, ADMIN) == 404


# --- Behaviour --------------------------------------------------------------


def test_templates_lists_names_and_fields(client: TestClient) -> None:
    response = client.get(TEMPLATES_URL, headers=ADMIN)
    assert response.status_code == 200
    entries = response.json()["templates"]
    assert [e["name"] for e in entries] == sorted(TEMPLATES)
    assert {"name": "help", "fields": []} in entries
    assert {"name": "unknown_command", "fields": ["command"]} in entries


def test_preview_escapes_data(client: TestClient) -> None:
    response = client.post(PREVIEW_URL, json=BODY, headers=ADMIN)
    assert response.status_code == 200
    html = "I don't know <code>/&lt;b&gt;x&lt;/b&gt;</code>. Try /help."
    assert response.json() == {"html": html, "length": len(html)}


def test_preview_unknown_template_is_404(client: TestClient) -> None:
    response = client.post(PREVIEW_URL, json={"template": "nope"}, headers=ADMIN)
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown template"}


def test_preview_missing_field_is_422_and_names_it(client: TestClient) -> None:
    response = client.post(PREVIEW_URL, json={"template": "unknown_command"}, headers=ADMIN)
    assert response.status_code == 422
    assert "command" in response.json()["detail"]


@pytest.mark.parametrize(
    "data",
    [
        {f"k{i}": "v" for i in range(21)},  # too many keys
        {"k" * 41: "v"},  # key too long
        {"command": "v" * 1001},  # value too long
    ],
)
def test_preview_enforces_data_limits(client: TestClient, data: dict[str, str]) -> None:
    response = client.post(
        PREVIEW_URL, json={"template": "unknown_command", "data": data}, headers=ADMIN
    )
    assert response.status_code == 422


def test_preview_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post(PREVIEW_URL, json={**BODY, "chatId": 1}, headers=ADMIN)
    assert response.status_code == 422


def test_preview_records_an_action(client: TestClient, migrated_test_db: str) -> None:
    client.post(PREVIEW_URL, json=BODY, headers=ADMIN)
    client.post(PREVIEW_URL, json={"template": "nope"}, headers=ADMIN)
    assert _outcomes(migrated_test_db) == ["ok", "rejected"]
