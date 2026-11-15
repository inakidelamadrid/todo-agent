"""Register or inspect the Telegram webhook (BE-039).

Thin CLI wrapper around aiogram's ``Bot``. Everything printed is a host, a
count, a date or a message — never the token, never the webhook secret,
never the full URL path.

Usage (via Makefile): ``make telegram-webhook url=…`` / ``make telegram-info``.
"""

import argparse
import asyncio
from collections.abc import Iterable
from urllib.parse import urlsplit

from aiogram import Bot
from aiogram.types import WebhookInfo

from app.settings import Settings, get_settings

WEBHOOK_PATH = "/integrations/telegram/webhook"
ALLOWED_UPDATES = ["message", "callback_query"]

_MISSING_TOKEN = "Telegram bot token is not set — add TELEGRAM_BOT_TOKEN to api/.env"
_MISSING_SECRET = (
    "Telegram webhook secret is not set — add TELEGRAM_WEBHOOK_SECRET to api/.env"
)


def format_webhook_info(info: WebhookInfo, *, redact: Iterable[str] = ()) -> str:
    """Pure: webhook status as host-only lines; never the full URL.

    ``redact`` lists secret values to blank out wherever they appear
    (defence in depth: even an error message echoing them stays safe).
    """

    def scrub(text: str) -> str:
        for value in redact:
            if value:
                text = text.replace(value, "***")
        return text

    lines = [
        f"url host: {urlsplit(info.url).hostname or '(none)'}",
        f"pending updates: {info.pending_update_count}",
        f"allowed updates: {', '.join(info.allowed_updates or []) or '(all)'}",
    ]
    if info.last_error_date:
        lines.append(f"last error: {info.last_error_date} — {scrub(info.last_error_message)}")
    else:
        lines.append("last error: (none)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram_webhook")
    subcommands = parser.add_subparsers(dest="command", required=True)
    set_cmd = subcommands.add_parser("set", help="register the webhook with Telegram")
    set_cmd.add_argument("--url", required=True, help="https:// base URL (ngrok tunnel)")
    subcommands.add_parser("info", help="show webhook status")
    return parser


def _require_token(settings: Settings) -> str:
    token = settings.telegram_bot_token.get_secret_value()
    if not token:
        raise SystemExit(_MISSING_TOKEN)
    return token


async def _run_set(settings: Settings, url: str) -> str:
    """Register `<url>/integrations/telegram/webhook`. Returns a host-only line."""
    full_url = url.rstrip("/") + WEBHOOK_PATH
    if not url.startswith("https://"):
        raise SystemExit("WEBHOOK url must start with https://")
    token = _require_token(settings)
    secret = settings.telegram_webhook_secret.get_secret_value()
    if not secret:
        raise SystemExit(_MISSING_SECRET)

    bot = Bot(token=token)
    try:
        await bot.set_webhook(
            full_url, secret_token=secret, allowed_updates=ALLOWED_UPDATES
        )
    finally:
        await bot.session.close()
    return f"Webhook set for {urlsplit(full_url).hostname}"


async def _run_info(settings: Settings) -> str:
    """Fetch webhook status and format it with secrets stripped."""
    token = _require_token(settings)
    bot = Bot(token=token)
    try:
        info = await bot.get_webhook_info()
    finally:
        await bot.session.close()
    return format_webhook_info(
        info,
        redact=(token, settings.telegram_webhook_secret.get_secret_value()),
    )


def main() -> None:
    """Entry point: parse args, dispatch, print the returned safe text."""
    args = build_parser().parse_args()
    run = _run_set if args.command == "set" else _run_info
    extra = (args.url,) if args.command == "set" else ()
    print(asyncio.run(run(get_settings(), *extra)))


if __name__ == "__main__":
    main()
