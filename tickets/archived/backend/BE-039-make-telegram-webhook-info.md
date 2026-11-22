# BE-039: make telegram-webhook and make telegram-info

- **Status:** done (implemented and verified on branch `idelamadrid/BE-039-telegram-webhook-info`; not committed — awaiting user approval)
- **Priority:** 5 — Very important (next in line); elevated by the user after BE-004 so webhook registration isn't blocked behind lower-priority work
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.5, §8
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** BE-004, BE-005
- **Can run in parallel with:** BE-006 onwards
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~12 min

## Goal

Two make targets register the webhook with Telegram through an ngrok URL and show its status, without ever printing a secret.

## Why this ticket exists

A webhook URL changes every time a free ngrok tunnel restarts, so registering it must be one command. `telegram-info` is the first thing to run when the bot seems silent.

## Read first

- `Makefile`: target style and the `check-env` guards.
- https://core.telegram.org/bots/api#setwebhook and `#getwebhookinfo`.
- Confirm every aiogram name used here against https://docs.aiogram.dev/ (v3) before coding; do not rely on memory.

## Design

- **Pattern:** Script at the edge: a thin command-line wrapper around a pure formatter.
- **Data flow:** `make telegram-webhook url=…` → `api/scripts/telegram_webhook.py set` → `bot.set_webhook(...)`; `make telegram-info` → `get_webhook_info` → `format_webhook_info` → stdout.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/scripts/__init__.py`, `api/scripts/telegram_webhook.py` (new): `argparse` with subcommands `set --url` and `info`.
- `Makefile` (changed): two targets with `##` help text.
- `api/tests/test_telegram_webhook_script.py` (new).

**`set`**

- `--url` must start with `https://`; the script appends `/integrations/telegram/webhook`.
- Calls `set_webhook(url, secret_token=<TELEGRAM_WEBHOOK_SECRET>, allowed_updates=["message", "callback_query"])`.
- Refuses to run, with a message pointing at `api/.env`, when the token or the secret is unset.
- Prints `Webhook set for <host>` (host only).

**`info`**

`format_webhook_info(info) -> str` (pure) prints: URL host, pending update count, last error date and message (if any), allowed updates. Never the token, never the secret, never the full URL path.

**Make**

```make
telegram-webhook: ## Register the dev webhook: make telegram-webhook url=https://<id>.ngrok.app
telegram-info: ## Show webhook status (no secrets)
```

## Steps

1. Write `format_webhook_info` and test it.
2. Write the two subcommands.
3. Add the make targets.

## Tests

- `test_format_webhook_info_shows_host_pending_and_last_error`
- `test_format_webhook_info_never_contains_secret_or_token`
- `test_set_rejects_http_url`
- `test_set_refuses_without_secret`
- `test_set_passes_secret_and_allowed_updates` (mocked `Bot`).

## Acceptance criteria

- [x] `make telegram-webhook url=…` registers the URL with the secret and the two allowed update types
- [x] `make telegram-info` output contains no secret
- [x] Both targets appear in `make help`
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With ngrok running (`ngrok http 8000`) and the dev bot's values in `api/.env`:

```bash
make telegram-webhook url=https://YOUR-ID.ngrok.app
```

```bash
make telegram-info
```

Expect your ngrok host, `pending: 0` and no last error.

## Review guide

Read the diff in this order, and check:

1. What the script prints: read every `print`.
2. The `allowed_updates` list.
3. The make targets pass nothing secret on the command line.

Things that should *not* be in the diff: prod deployment; BotFather steps.

## Out of scope

- Creating the bots and setting commands → BE-040.

## Assumptions

- ngrok is the tunnel, as answered (question 2). Production hosting is not decided and not covered.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- **Execution note:** the dependency BE-005 (`aiogram`) was not done, so it was implemented first on its own branch (`idelamadrid/BE-005-aiogram-and-update-fixtures`); this branch sits on top of it — **review/merge BE-005's PR before this one**.
- aiogram v3.32 API verified by introspection before coding: `Bot.set_webhook(url, *, secret_token, allowed_updates)`, `get_webhook_info() -> WebhookInfo`, and the `session.close()` cleanup contract.
- `format_webhook_info` gained a `redact=` denylist beyond the ticket's spec: a test with a secret embedded in `last_error_message` showed the pass-through formatter would echo it. Output now scrubs known secret values (`***`) wherever they appear.
- `--url` must start with `https://`; the script appends `/integrations/telegram/webhook` and trims a trailing slash. Missing token/secret → `SystemExit` with a pointer at `api/.env` (no values echoed).
- **Live-verified with the real dev bot:** probe webhook registered, `make telegram-info` showed the host, `pending: 0`, `allowed updates: message, callback_query`, no error; probe webhook then deleted (`delete_webhook`) to leave Telegram idle state.
- `make api-test` → 106 passed (7 of them new, all from this ticket's Test list plus boundary cases).
- Open question for review: `make telegram-webhook` with no `url=` fails with the usage line (exit 1) — verified.
