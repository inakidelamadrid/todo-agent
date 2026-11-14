"""Shared test fixtures.

``API_KEYS`` is given a session fallback *before* importing the app, because
``app.main`` builds the application at import time (fail-fast on missing
config). Individual tests override it via ``monkeypatch`` as needed.
"""

import os
from collections.abc import Callable

os.environ.setdefault("API_KEYS", "test-key-1,test-key-2")

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import require_api_key
from app.settings import get_settings

KEY_ONE = "test-key-1"
KEY_TWO = "test-key-2"
PROTECTED_PROBE_PATH = "/__test-protected"


def _protected_probe_router() -> APIRouter:
    """A protected route registered only in tests — never shipped."""
    router = APIRouter(dependencies=[Depends(require_api_key)])

    @router.get(PROTECTED_PROBE_PATH)
    def _probe() -> dict[str, bool]:
        return {"ok": True}

    return router


@pytest.fixture()
def make_client(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], TestClient]:
    """Build a TestClient for a given comma-separated API_KEYS value."""

    def _make(api_keys: str) -> TestClient:
        monkeypatch.setenv("API_KEYS", api_keys)
        get_settings.cache_clear()
        app: FastAPI = create_app()
        app.include_router(_protected_probe_router())
        return TestClient(app)

    yield _make
    get_settings.cache_clear()


@pytest.fixture()
def client(make_client: Callable[[str], TestClient]) -> TestClient:
    return make_client(f"{KEY_ONE},{KEY_TWO}")
