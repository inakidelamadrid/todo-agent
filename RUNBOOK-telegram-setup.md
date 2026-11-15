# Telegram Setup Runbook

How to obtain the three values the API needs for its Telegram integration
(`api/.env`, gitignored — never commit real values):

- `TELEGRAM_BOT_TOKEN` — identifies our bot
- `TELEGRAM_WEBHOOK_SECRET` — guards our webhook endpoint
- `TELEGRAM_ALLOWED_USER_ID` — the only Telegram user the bot answers

Everything below can be done from Telegram's web UI: https://web.telegram.org

## 1. Bot token (from @BotFather)

1. Open https://web.telegram.org and log in.
2. Search for **@BotFather** (verified checkmark) and open the chat.
3. Send `/newbot`, then follow the prompts:
   - **Name:** display name, e.g. `Todo Agent`
   - **Username:** must end in `bot`, e.g. `todo_agent_bot`
4. BotFather replies with a token like `123456789:AAE...`.
   Copy it into `api/.env`:

   ```
   TELEGRAM_BOT_TOKEN=<paste token here>
   ```

Keep the token secret: anyone holding it controls the bot. If it leaks,
revoke it with `/revoke` in the same BotFather chat and set the new one.

## 2. Your user ID (from @userinfobot)

1. In Telegram web, search for **@userinfobot** and open the chat.
2. Send `/start`.
3. It replies with `Id: <number>`. Copy the number into `api/.env`:

   ```
   TELEGRAM_ALLOWED_USER_ID=<the number>
   ```

This is a *user* ID, not a chat ID. The API ignores updates from anyone else.

## 3. Webhook secret (generated locally, never from a website)

Telegram sends this value back to us in every webhook request; we reject any
request without it. Generate it on your machine:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output into `api/.env`:

```
TELEGRAM_WEBHOOK_SECRET=<generated value>
```

Rules: 16–256 characters of `A-Z a-z 0-9 _ -` (the generator above complies).
The app refuses to start with a secret that violates them.

## 4. Validate

Start the databases, then check that the integration is seen as enabled —
this prints a boolean only, never any value:

```bash
make telegram-check
```

Expected: `telegram_enabled: True`. If `False`, one of the three variables
is missing from `api/.env` — recheck steps 1–3.

A quick API smoke check with the same values:

```bash
make db-up && make api-dev   # must start without errors
curl -s -H "X-API-Key: <your key>" http://127.0.0.1:8000/health
```

## What this runbook does *not* cover

Registering the webhook URL with Telegram (`setWebhook`) and exposing the API
to the internet are separate, later steps — see ticket
`tickets/backend/BE-039-make-telegram-webhook-info.md` and
`tickets/backend/BE-040-bot-setup-runbook-commands.md`.
