"""Hourly limit for playground test messages (BE-079). Pure."""

TEST_MESSAGES_PER_HOUR = 10


def may_send(sent_last_hour: int, limit: int = TEST_MESSAGES_PER_HOUR) -> bool:
    return sent_last_hour < limit
