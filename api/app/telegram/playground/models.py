"""playground_actions: who used which playground tool, and how it ended (BE-069).

Audit only — no request body, message text, template data or chat ID is
ever stored. The hourly send-test-message limit (BE-079) counts rows here;
there is intentionally no column that could hold message content.
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

TOOLS = ("updates", "explain", "replay", "template_preview", "test_message")
OUTCOMES = ("ok", "failed", "rejected")


class PlaygroundAction(Base):
    __tablename__ = "playground_actions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    admin_user_id: Mapped[str] = mapped_column(String(64))
    tool: Mapped[str] = mapped_column(String(20))
    outcome: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        CheckConstraint(f"tool IN {TOOLS}", name="ck_playground_actions_tool"),
        CheckConstraint(f"outcome IN {OUTCOMES}", name="ck_playground_actions_outcome"),
        Index("ix_playground_actions_tool_created_at", "tool", "created_at"),
    )
