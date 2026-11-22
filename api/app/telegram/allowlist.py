"""Allowlist: only the owner's updates are processed (BE-009).

The webhook secret proves a request is from Telegram; this predicate proves
the update is from the owner. They are separate checks. Unconfigured means
nobody is allowed (fail closed).

The bot is private-only: in a private chat Telegram's ``chat.id`` equals the
user's ``id``, so a group chat the owner happens to be in is also rejected.
"""

from app.telegram.inbound import InboundUpdate


def is_allowed(update: InboundUpdate, allowed_user_id: int | None) -> bool:
    """True only for an update sent by the allowed user in their own chat."""
    if allowed_user_id is None:
        return False
    if update.user_id != allowed_user_id:
        return False
    return update.chat_id is None or update.chat_id == allowed_user_id
