"""Telegram service: the one way outbound text leaves the app (BE-021).

Facade over render + send. ``reply`` answers something the owner just sent,
so it goes out immediately: no quiet hours, caps or grouping. Messages the
app initiates go through ``send`` and the notification policy (BE-030),
which will live here too — "all outbound goes through the Telegram service"
(EPIC-008 §8).
"""

from app.telegram.handlers import Reply
from app.telegram.sender import OutgoingMessage, SentMessage, TelegramSender
from app.telegram.templates import render


async def reply(sender: TelegramSender, chat_id: int, reply: Reply) -> SentMessage:
    """Render ``reply`` and send it to ``chat_id``. No buttons yet (BE-023)."""
    return await sender.send(OutgoingMessage(chat_id=chat_id, text=render(reply.template, reply.data)))
