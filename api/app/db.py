"""Database engine and session plumbing.

All I/O lives here at the edge: the engine is created once in the app
lifespan and disposed on shutdown; ``get_session`` gives each request one
transaction.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import Settings


class Base(DeclarativeBase):
    pass


def build_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


async def dispose_engine(engine: AsyncEngine) -> None:
    await engine.dispose()


def _engine(request: Request) -> AsyncEngine:
    return request.app.state.db_engine


async def get_session(
    engine: Annotated[AsyncEngine, Depends(_engine)],
) -> AsyncIterator[AsyncSession]:
    """One session + one transaction per request (rolls back on error)."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            yield session
