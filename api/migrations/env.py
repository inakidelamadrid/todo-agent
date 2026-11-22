"""Alembic environment (async, asyncpg).

URL resolution order:
1. ``sqlalchemy.url`` set programmatically (tests point at per-worker DBs).
2. ``Settings`` — reads ``.env`` and the repo-root ``../.env.db``.

The URL is never logged: SQLAlchemy echo stays off and alembic.ini
configures no URL output. ``api_keys`` is satisfied with a dummy value
because migrations never serve requests.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Register ORM tables on Base.metadata.
from app.bills import models as _models  # noqa: F401
from app.db import Base
from app.settings import Settings
from app.telegram import models as _telegram_models  # noqa: F401
from app.telegram.playground import models as _playground_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    return Settings(api_keys="alembic-migrations").database_url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run_sync_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _url()
    engine = async_engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
