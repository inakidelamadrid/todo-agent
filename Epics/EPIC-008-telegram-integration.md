# EPIC-008: Telegram integration (infra)

- **Status:** draft
- **Type:** infrastructure (formalizes foundation **F-7 Telegram channel**)
- **Owner:** Ignacio
- **Depends on:** F-2 Scoped API keys, F-6 Scheduler & notifications (Redis queue)
- **Used by:**
  - EPIC-002: expenses;
  - EPIC-003: brain dump, `/now`, focus check-ins;
  - EPIC-004: grouped reminders and the digest;
  - EPIC-005: reset invite and summary;
  - EPIC-006: `/vault` uploads;
  - EPIC-001: payer alerts. The ex-spouse is never contacted on Telegram unless decided otherwise.

## 1. Summary

One private Telegram bot as the app's **conversational front door** and its **main push channel**:

1. **Inbound:** receive my texts, voice notes, photos, documents, commands and button taps; verify them; de-duplicate; and **route** each update to the right feature (brain dump, expense, vault, command, or a callback for a previous message).
2. **Outbound:** a single `TelegramService.send(...)` used by every feature for messages with inline buttons, grouped reminders, edits ("✓ done") and digests. It respects quiet hours, pause and rate limits.
3. **AI parsing in n8n:** n8n keeps the AI-heavy flows (transcription, OCR, parsing). The **API stays the source of truth** for rules, idempotency and data.

## 2. Goals

- Only I can use the bot. Everything else is ignored silently.
- Every update is processed **exactly once** (Telegram retries can't create duplicates).
- One routing table decides where each message goes, and it's easy to extend when a new epic adds a command.
- Every outbound message goes through one service, with caps, quiet hours and pause enforced centrally.
- The setup can move from n8n to the API (or back) without changing feature code.

## 3. Non-goals

- A multi-user or group bot.
- Telegram Mini Apps (possible later for quick views).
- Telegram payments.

## 4. Architecture decision (to confirm)

| Option | Inbound webhook goes to | Pros | Cons |
|---|---|---|---|
| **A. n8n-first** | n8n Telegram Trigger → n8n routes → n8n calls the API | Fastest to build; visual flows; matches EPIC-002/003 drafts | Routing and allowlist logic live in n8n, outside tests and versioning |
| **B. API-first (recommended long-term)** | `POST /integrations/telegram/webhook` on the API → API validates, de-dupes and routes → calls n8n webhooks only for AI parsing → the API replies | Allowlist, idempotency and routing are tested and versioned; n8n becomes swappable | Needs the API reachable over public HTTPS; slightly more backend work |

**Recommendation:** start with **B**, or move to it quickly. The secret-token check, the allowlist and idempotency belong in tested code. n8n stays for transcription, OCR and LLM parsing behind authenticated webhooks. Outbound always goes through the API's `TelegramService`, in both options.

Only one webhook can be registered per bot. Use **separate bots for dev and prod** (e.g. `@todo_agent_dev_bot`) so local testing never touches the real bot.

## 5. Requirements

### 5.1 Bot setup
- Create the bots with BotFather (dev + prod), with a name, description, profile photo and **command list**:
  - `/now`: what to do now (EPIC-003)
  - `/inbox`: inbox count + link (EPIC-003)
  - `/done`: finish the current focus task (EPIC-003)
  - `/today`, `/month`: spending totals (EPIC-002)
  - `/radar`: what's coming up (EPIC-004)
  - `/reset`: start the weekly reset (EPIC-005)
  - `/vault`: next photo or PDF goes to the vault (EPIC-006)
  - `/undo`: undo the last action
  - `/pause`, `/resume`: pause notifications
  - `/help`
- Privacy mode on. The bot can't be added to groups (`setMyDefaultAdministratorRights` / `can_join_groups=false`).
- Bot tokens live in backend env and n8n credentials only, never in the frontend or the repo.

### 5.2 Inbound
- **Webhook:**
  - HTTPS URL registered with `secret_token`;
  - every request must carry the matching `X-Telegram-Bot-Api-Secret-Token` header, otherwise 401;
  - `allowed_updates` limited to `message` and `callback_query`.
- **Allowlist:**
  - process updates only from my Telegram **user ID** (and chat ID);
  - drop everything else with a 200 response, no reply, logged as a counter.
- **Idempotency:**
  - `update_id` is unique and stored for N days;
  - a repeat returns 200 without reprocessing;
  - downstream records use `sourceRef = telegram:<chat_id>:<message_id>`.
- **Router**, in order:
  1. `callback_query`: decode signed callback data → the feature action (e.g. `expense:change-category:<id>`).
  2. Commands (`/now`, `/vault`, …) → the feature handler.
  3. **Pending mode:** e.g. after `/vault`, the next photo goes to the vault (session state in Redis with a TTL).
  4. Caption keywords ("vault", "gasto") → that feature.
  5. Default:
     - text and voice → brain dump (EPIC-003), whose AI split also detects expenses;
     - photo → ask "Receipt, document or note?" with buttons, unless it's confidently classified.
- **Media:**
  - download through `getFile` server-side;
  - limit size and type;
  - store per feature (F-4/Drive) or discard after parsing (per the feature's policy).
- **Response time:** acknowledge Telegram within a few seconds. Heavy work (AI, OCR) runs async, then the bot replies or edits a "Working on it…" message.

### 5.3 Outbound
- `TelegramService.send(chat, template, data, buttons?, category, idempotency_key)`, plus `edit` and `delete`.
- **Templates:** short, ES/EN, Telegram MarkdownV2 or HTML, with escaping handled centrally.
- **Inline buttons:**
  - callback data is **signed** (HMAC) and compact (≤64 bytes: action + ID + signature), so forged or replayed taps are rejected;
  - buttons expire after N days.
- **Central policies:**
  - **Quiet hours** and **pause**: messages are deferred, not dropped, except categories marked urgent.
  - **Per-category caps** (e.g. 1 grouped radar message per day).
  - **Grouping window:** messages to the same chat within X minutes can merge.
  - **Telegram rate limits:** a queue with throttling; on 429, honour `retry_after`.
- **Failure handling:** retries with backoff. If Telegram is unreachable for longer than N minutes, important categories fall back to email (EPIC-007).

### 5.4 n8n contract (AI flows)
- The API calls n8n with **authenticated webhooks** (shared secret or HMAC header) for:
  - `transcribe(voice)`;
  - `ocr(image)`;
  - `parse_dump(text)`;
  - `parse_expense(text)`;
  - `extract_document(image)`.
- n8n returns strict JSON (schemas in the repo). n8n never writes data directly in option B; under option A it uses a scoped API key per feature (F-2).
- Workflows are exported as JSON to `integrations/n8n/` and versioned.

### 5.5 Environments and local development
- The dev bot plus a tunnel (cloudflared or ngrok) to the local API; a `make telegram-webhook` target registers or refreshes the webhook URL with the secret.
- `make telegram-info` shows webhook status (`getWebhookInfo`: pending updates, last error) without printing secrets.
- **Tests:** recorded update payloads (text, voice, photo, command, callback) to exercise the router, allowlist and idempotency.

### 5.6 Observability
- Structured logs: update type, route chosen, latency, outcome. Message text is never logged.
- Health indicators: webhook status, queue depth, last successful send, error rate. Shown in a small admin or status page, and alerted on failure.

## 6. Data model (draft)

| Entity | Key fields |
|---|---|
| `TelegramUpdate` | updateId (unique), chatId, messageId?, type, route, status (`processed`/`ignored`/`failed`), receivedAt |
| `TelegramSession` (Redis, TTL) | chatId, pendingMode (`vault`/`expense`/…), context, expiresAt |
| `TelegramOutbound` | id, chatId, template, category, status (`queued`/`sent`/`deferred`/`failed`), telegramMessageId?, idempotencyKey, attempts, scheduledFor? |
| `NotificationPolicy` | quietHours, pausedUntil?, perCategoryCaps, groupingWindowMinutes |

## 7. Security and privacy

- Secret-token webhook validation, a user-ID allowlist, signed callback data, and rate limits on the webhook.
- Bot tokens and n8n secrets only in env and credential stores. Rotation is documented (BotFather `/revoke`).
- Minimal content in messages:
  - titles and dates by default;
  - amounts and personal details only where enabled;
  - **never** document numbers or child support evidence.
- Media is processed server-side and retained only per feature policy. No message text in logs.

## 8. Epic acceptance criteria

- [ ] Only my account gets responses. Messages from others are ignored and counted.
- [ ] Duplicate deliveries (same `update_id`) never cause duplicate records.
- [ ] Text, voice, photo, document, every listed command and every callback button route to the correct feature, covered by router tests with recorded payloads.
- [ ] All outbound messages go through `TelegramService`. Quiet hours, pause, caps, grouping and 429 back-off are enforced centrally.
- [ ] Tampered or expired callback buttons are rejected.
- [ ] Dev and prod bots are separate; `make telegram-webhook` and `make telegram-info` work locally through a tunnel.
- [ ] AI work runs async, so the user sees "Working on it…" immediately, then the result.

## 9. Proposed ticket breakdown (draft)

- **Ops:**
  - Bots (dev/prod) + command list + privacy settings.
  - Tunnel + `make telegram-webhook` / `telegram-info`.
  - n8n AI flows exported to `integrations/n8n/`.
- **Backend:**
  - Webhook endpoint (secret, allowlist, idempotency).
  - Router + session state (Redis).
  - `TelegramService` outbound + templates + signed callbacks.
  - Central notification policy (quiet hours, pause, caps, grouping) shared with F-6.
  - n8n client (HMAC) + response schemas.
  - Observability + health.
- **Frontend:** notification settings (quiet hours, pause, categories) and a Telegram connection status.

## 10. Open questions (answer in place)

1. Architecture: A (n8n-first) or B (API-first)?
   - Answer:
2. Where is the API reachable over public HTTPS for the webhook (tunnel, VPS, cloud)?
   - Answer:
3. Your Telegram user ID (or should the bot capture it on a one-time `/start <code>` pairing)?
   - Answer:
4. Bot reply language: Spanish, English, or mirror the message?
   - Answer:
5. Default quiet hours, and which categories may break through them (e.g. "due today" bills)?
   - Answer:
6. Should important notifications fall back to email when Telegram fails?
   - Answer:
7. Keep voice notes and photos after parsing, or discard them by default?
   - Answer:
