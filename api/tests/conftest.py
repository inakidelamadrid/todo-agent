"""Shared test fixtures.

``API_KEYS`` is given a session fallback *before* importing the app, because
``app.main`` builds the application at import time (fail-fast on missing
config). Individual tests override it via ``monkeypatch`` as needed.
"""

import os
from collections.abc import Callable

os.environ.setdefault("API_KEYS", "test-key-1,test-key-2")

import asyncio
import re
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import require_api_key
from app.settings import Settings, get_settings

KEY_ONE = "test-key-1"
KEY_TWO = "test-key-2"
PROTECTED_PROBE_PATH = "/__test-protected"

_API_DIR = Path(__file__).resolve().parent.parent


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


# ---------------------------------------------------------------------------
# Integration fixtures: one real, migrated, disposable database per xdist
# worker. The dev database is never touched. If Postgres is down, we fail
# loudly with instructions instead of silently skipping.
# ---------------------------------------------------------------------------


def _dsn(settings: Settings, database: str) -> str:
    return (
        f"postgresql+asyncpg://{settings.postgres_user}:"
        f"{settings.postgres_password.get_secret_value()}@"
        f"{settings.postgres_host}:{settings.postgres_port}/{database}"
    )


async def _admin_exec(settings: Settings, statement: str, database: str = "postgres") -> None:
    """Run one statement against an admin connection."""
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password.get_secret_value(),
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=database,
        )
    except (OSError, asyncpg.PostgresError) as exc:
        raise RuntimeError(
            f"Postgres is not reachable at {settings.postgres_host}:{settings.postgres_port} "
            f"({type(exc).__name__}). Start it with `make db-up`, then re-run the tests."
        ) from None
    try:
        await conn.execute(statement)
    finally:
        await conn.close()


def _upgrade_head(url: str) -> None:
    cfg = Config(str(_API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def migrated_test_db(worker_id: str) -> str:
    """`<dev_db>_test_<worker>`: created, migrated, dropped at session end."""
    settings = Settings(api_keys="test-suite")
    db_name = f"{settings.postgres_db}_test_{worker_id}"
    assert re.fullmatch(r"[a-z0-9_]+", db_name), f"unsafe test db name: {db_name!r}"

    asyncio.run(_admin_exec(settings, f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    asyncio.run(_admin_exec(settings, f'CREATE DATABASE "{db_name}"'))
    _upgrade_head(_dsn(settings, db_name))
    yield db_name
    asyncio.run(_admin_exec(settings, f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))


@pytest.fixture()
def db_client(monkeypatch: pytest.MonkeyPatch, migrated_test_db: str) -> TestClient:
    """App client wired to this worker's migrated test database."""
    monkeypatch.setenv("API_KEYS", KEY_ONE)
    monkeypatch.setenv("POSTGRES_DB", migrated_test_db)
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as test_client:  # lifespan: engine up/down
            yield test_client
    finally:
        get_settings.cache_clear()
