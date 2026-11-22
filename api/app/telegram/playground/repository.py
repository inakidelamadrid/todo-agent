"""Async persistence for the playground action log (BE-069).

Functions take a session and do exactly one thing. No HTTP, no FastAPI.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.telegram.playground.models import PlaygroundAction


async def record_action(
    session: AsyncSession, admin_user_id: str, tool: str, outcome: str
) -> UUID:
    """Insert one row and return its id.

    Every attempt is recorded, including ``rejected`` and ``failed`` — the
    row is an audit trail, not a success counter; the BE-079 hourly limit
    deliberately counts only ``outcome="ok"`` via ``count_actions_since``.

    Flush only, no commit: the caller owns the transaction (request-scoped
    sessions commit on success — see ``app.db.get_session``).
    Unknown tools or outcomes are rejected by the table's CHECK constraints
    (IntegrityError on flush).
    """
    action = PlaygroundAction(admin_user_id=admin_user_id, tool=tool, outcome=outcome)
    session.add(action)
    await session.flush()
    return action.id


async def count_actions_since(
    session: AsyncSession, tool: str, since: datetime, outcome: str = "ok"
) -> int:
    """How many ``tool`` calls have ended with ``outcome`` since ``since``
    (inclusive). Backs the hourly send-test-message limit (BE-079), which is
    why it defaults to ``outcome="ok"``: rejected and failed attempts are
    recorded but never counted toward the limit."""
    stmt = select(func.count(PlaygroundAction.id)).where(
        PlaygroundAction.tool == tool,
        PlaygroundAction.outcome == outcome,
        PlaygroundAction.created_at >= since,
    )
    return (await session.execute(stmt)).scalar_one()
