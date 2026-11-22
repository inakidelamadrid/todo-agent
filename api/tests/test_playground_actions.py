"""Integration tests for playground_actions (BE-069).

Each worker gets its own migrated, disposable database (conftest's
``migrated_test_db``). Async code is exercised through asyncio.run, the same
pattern conftest uses for database administration.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings
from app.telegram.playground.models import OUTCOMES, TOOLS, PlaygroundAction
from app.telegram.playground.repository import count_actions_since, record_action

T = TypeVar("T")

_API_DIR = Path(__file__).resolve().parent.parent


def _settings(database: str) -> Settings:
    return Settings(api_keys="test-suite", postgres_db=database)


def _run(database: str, scenario: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async def _with_session() -> T:
        engine = create_async_engine(_settings(database).database_url)
        try:
            async with AsyncSession(engine) as session:
                return await scenario(session)
        finally:
            await engine.dispose()

    return asyncio.run(_with_session())


def test_record_action_inserts_a_row_and_returns_its_id(migrated_test_db: str) -> None:
    async def scenario(session: AsyncSession) -> tuple[UUID, PlaygroundAction]:
        action_id = await record_action(session, "user_owner", "updates", "ok")
        row = (await session.scalars(select(PlaygroundAction))).one()
        return action_id, row

    action_id, row = _run(migrated_test_db, scenario)
    assert isinstance(action_id, UUID)
    assert row.id == action_id
    assert row.admin_user_id == "user_owner"
    assert row.tool == "updates"
    assert row.outcome == "ok"
    assert row.created_at.tzinfo is not None  # timestamptz


def test_unknown_tool_or_outcome_is_rejected_by_the_database(
    migrated_test_db: str,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        for bad_tool, bad_outcome in [("shell", "ok"), ("updates", "exploded")]:
            with pytest.raises(IntegrityError):
                await record_action(session, "user_owner", bad_tool, bad_outcome)
            await session.rollback()

    _run(migrated_test_db, scenario)


def test_count_actions_since_counts_only_that_tool_outcome_and_window(
    migrated_test_db: str,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        await record_action(session, "user_owner", "test_message", "ok")
        await record_action(session, "user_owner", "test_message", "ok")
        # Same window, but different tool or outcome: must not be counted.
        await record_action(session, "user_owner", "test_message", "failed")
        await record_action(session, "user_owner", "explain", "ok")

        now = datetime.now(timezone.utc)
        assert await count_actions_since(
            session, "test_message", since=now - timedelta(hours=1)
        ) == 2
        assert await count_actions_since(
            session, "test_message", since=now - timedelta(hours=1), outcome="failed"
        ) == 1
        # A future window excludes the just-recorded rows.
        assert await count_actions_since(
            session, "test_message", since=now + timedelta(hours=1)
        ) == 0

    _run(migrated_test_db, scenario)


async def _fetchval(database: str, sql: str) -> Any:
    conn = await asyncpg.connect(
        dsn=_settings(database).database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
    )
    try:
        return await conn.fetchval(sql)
    finally:
        await conn.close()


def test_db_check_constraints_match_model_constants(migrated_test_db: str) -> None:
    """Drift guard (review note): the migration freezes the CHECK lists, so
    adding a value to TOOLS/OUTCOMES without a migration altering the
    constraint fails here instead of silently diverging."""
    for constraint, values in [
        ("ck_playground_actions_tool", TOOLS),
        ("ck_playground_actions_outcome", OUTCOMES),
    ]:
        definition: str = asyncio.run(
            _fetchval(
                migrated_test_db,
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                f"WHERE conname = '{constraint}'",
            )
        )
        assert definition is not None, f"{constraint} missing in the database"
        for value in values:
            assert f"'{value}'" in definition, f"{value} missing in {constraint}"
        assert definition.count("::character varying") == len(values), (
            f"{constraint} holds values the model has dropped"
        )


def test_migration_upgrade_and_downgrade(migrated_test_db: str) -> None:
    cfg = Config(str(_API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", _settings(migrated_test_db).database_url)

    async def _table_exists() -> bool:
        return bool(
            await _fetchval(
                migrated_test_db,
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'playground_actions')",
            )
        )
    try:
        command.downgrade(cfg, "-1")
        assert asyncio.run(_table_exists()) is False
        command.upgrade(cfg, "head")
        assert asyncio.run(_table_exists()) is True
    finally:
        # Always leave the worker's database at head for the other tests.
        command.upgrade(cfg, "head")
