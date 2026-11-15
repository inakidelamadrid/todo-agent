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

## Registering the webhook against the live bot (BE-039)

Once steps 1–3 are done and `make telegram-check` prints
`telegram_enabled: True`, you can point Telegram at your local API through a
public tunnel. Everything below prints hosts and counts only — never the
token, secret or full URL.

### 1. Expose the API through ngrok

A free ngrok URL changes on every restart, so re-register whenever it does.

```bash
make db-up
make api-dev                 # terminal 1: API on 127.0.0.1:8000
ngrok http 8000              # terminal 2: copy the https://<id>.ngrok.app URL
```

### 2. Register the webhook

```bash
make telegram-webhook url=https://<id>.ngrok.app
```

Expected output (host only):

```
Webhook set for <id>.ngrok.app
```

The command fails fast with a usage line when `url=` is missing, rejects
`http://`, and refuses with a pointer at `api/.env` when the token or secret
is unset. Telegram now delivers `message` and `callback_query` updates to
`<url>/integrations/telegram/webhook` (that route is wired in a later ticket
— until then Telegram gets 404s, which is expected and harmless).

### 3. Inspect the webhook — first tool when the bot seems silent

```bash
make telegram-info
```

Healthy output:

```
url host: <id>.ngrok.app
pending updates: 0
allowed updates: message, callback_query
last error: (none)
```

What each symptom means:

| Symptom | Meaning | Action |
|---|---|---|
| `url host: (none)` | webhook not registered | run step 2 |
| `pending updates` growing | Telegram delivers but we error/time out | check the API is running behind the tunnel |
| `last error:` set | Telegram's last delivery failed, with its message | fix the cause (usually a dead tunnel), then re-run step 2 |
| host ≠ current ngrok URL | stale tunnel URL | re-run step 2 with the new URL |

### 4. Clean up when done

Closing the ngrok terminal leaves Telegram posting to a dead URL — safe (errors
accumulate in `last error`, updates queue briefly), but unregistering leaves
the bot fully idle. Run this when you close the tunnel (or anytime; it is
idempotent and independent of the tunnel's state):

```bash
make telegram-bot-cleanup
```

```
Webhook unregistered (bot is idle).
```

