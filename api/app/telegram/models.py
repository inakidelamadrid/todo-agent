"""telegram_updates: exactly-once memory for inbound updates (BE-010).

Telegram re-sends an update when our response is slow or fails; Telegram's
own ``update_id`` is the primary key, so the database itself refuses
duplicates. No message text, caption or callback data is ever stored.
"""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.telegram.inbound import UpdateKind

STATUSES = ("received", "processed", "failed")


class TelegramUpdate(Base):
    __tablename__ = "telegram_updates"

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(20))
    route: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(12), default="received")
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            f"kind IN {tuple(k.value for k in UpdateKind)}",
            name="ck_telegram_updates_kind",
        ),
        CheckConstraint(f"status IN {STATUSES}", name="ck_telegram_updates_status"),
        # The 30-day clean-up (BE-055) deletes through this index.
        Index("ix_telegram_updates_received_at", "received_at"),
    )
