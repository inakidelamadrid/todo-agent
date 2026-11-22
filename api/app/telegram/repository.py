"""Async persistence for telegram_updates (BE-011).

"Have we seen this?" and "remember it" are one atomic statement:
``INSERT … ON CONFLICT DO NOTHING RETURNING``. A pair of SELECT-then-INSERT
would let two simultaneous retries both pass the check.

No FastAPI imports; functions take a session and do exactly one thing.
"""

from datetime import datetime

from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.telegram.inbound import InboundUpdate
from app.telegram.models import TelegramUpdate


async def claim_update(session: AsyncSession, update: InboundUpdate) -> bool:
    """Atomic claim: True the first time an ``update_id`` is seen, False for
    every later delivery. Commits, so the claim survives a failing handler.
    """
    stmt = (
        pg_insert(TelegramUpdate)
        .values(
            update_id=update.update_id,
            chat_id=update.chat_id,
            message_id=update.message_id,
            kind=update.kind.value,
        )
        .on_conflict_do_nothing(index_elements=["update_id"])
        .returning(TelegramUpdate.update_id)
    )
    claimed = (await session.execute(stmt)).scalar_one_or_none()
    if claimed is not None:
        await session.commit()
    return claimed is not None


async def mark_update(
    session: AsyncSession, update_id: int, status: str, route: str = ""
) -> None:
    """Record how an update ended (``processed`` / ``failed``) and where it
    went. Commits. Unknown ``update_id`` is a no-op."""
    stmt = (
        update(TelegramUpdate)
        .where(TelegramUpdate.update_id == update_id)
        .values(status=status, route=route)
    )
    await session.execute(stmt)
    await session.commit()


async def delete_updates_before(session: AsyncSession, cutoff: datetime) -> int:
    """Delete rows received before ``cutoff``; returns the count. Commits.
    Nothing calls it yet — the daily clean-up job (BE-055) will, with a
    30-day cutoff."""
    result = await session.execute(
        delete(TelegramUpdate).where(TelegramUpdate.received_at < cutoff)
    )
    await session.commit()
    return result.rowcount
