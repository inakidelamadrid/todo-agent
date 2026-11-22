# EPIC-008: Telegram integration (infra)

- **Status:** in-tickets
- **Type:** infrastructure (formalizes foundation **F-7 Telegram channel**)
- **Owner:** Ignacio
- **Depends on:** F-2 Scoped API keys, F-6 Scheduler & notifications (Redis queue); EPIC-009 User login for the debugger playground (5.7)
- **Split out on 2026-11-22:** the notification policy and outbox → [EPIC-010](EPIC-010-telegram-notification-policy-outbox.md); the playground's route explainer and replay → [EPIC-011](EPIC-011-telegram-debugger-explain-replay.md).
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
2. **Outbound:** one Telegram service for every message. Here: `service.reply`, which renders a template and sends it immediately (replies and playground test messages), plus edits and inline buttons. App-initiated messages (`service.send`, with quiet hours, pause, caps and the outbox) are [EPIC-010](EPIC-010-telegram-notification-policy-outbox.md).
3. **AI parsing in n8n:** n8n keeps the AI-heavy flows (transcription, OCR, parsing). The **API stays the source of truth** for rules, idempotency and data.

4. **Debugger playground (admin only):** a screen in the web app where an admin can watch what the bot received, preview templates, and send a test message to their own chat. See 5.7. The route explainer and replay are [EPIC-011](EPIC-011-telegram-debugger-explain-replay.md).

## 2. Goals

- Only I can use the bot. Everything else is ignored silently.
- Every update is processed **exactly once** (Telegram retries can't create duplicates).
- One routing table decides where each message goes, and it's easy to extend when a new epic adds a command.
- Every outbound message goes through one service (policies for app-initiated messages: EPIC-010).
- The setup can move from n8n to the API (or back) without changing feature code.
- When the bot does something unexpected, an admin can find out *why* from the web app, without reading server logs or poking the production bot by hand.

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
- `service.reply(sender, chat_id, reply)`: render and send immediately, no queue and no policy. Used for replies and playground test messages. Plus `edit` and `delete`.
- `service.send(...)` for app-initiated messages, with the outbox and policies: EPIC-010.
- **Templates:** short, ES/EN, Telegram MarkdownV2 or HTML, with escaping handled centrally.
- **Inline buttons:**
  - callback data is **signed** (HMAC) and compact (≤64 bytes: action + ID + signature), so forged or replayed taps are rejected;
  - buttons expire after N days.
- **Central policies, outbox, 429 back-off and email fallback:** moved to [EPIC-010](EPIC-010-telegram-notification-policy-outbox.md).

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
- Health indicators (status endpoint and card): moved to EPIC-010, because queue depth needs the outbox.

### 5.7 Debugger playground (admin only)

A screen for understanding and testing the bot. It explains decisions the code already makes; it adds no second way to do them. Every tool calls the same pure functions the webhook and the sender use.

**Who can open it**

- **Admins only.** An admin is a signed-in person (EPIC-009 `User`) whose Clerk user ID is in `ADMIN_USER_IDS` (comma-separated, in `api/.env`). More admins are expected later, so it is a list from the start. A machine with an API key is never an admin. An empty list means nobody is an admin.
- **First admin:** the owner's account (Ignacio's Google sign-in). The identifying value is set in the environment by the human; it is not written in the repository.
- New shared dependency `require_admin`, built on `require_user`: no credentials or a bad token → `401`; a signed-in non-admin or a machine → `403`. Every playground endpoint is mounted behind it, under `/admin/telegram/…`.
- `GET /me` gains `"roles": ["admin"]` (or `[]`), so the web app can hide the entry point. Hiding is a courtesy; the API check is the one that counts.
- The playground is off unless `TELEGRAM_PLAYGROUND_ENABLED=true`. When off, its endpoints answer `404`.
- **Development only.** It is never available in production: the app refuses to start if the switch is on in a production environment.

**Tools**

| Tool | What it shows or does | Side effects |
|---|---|---|
| **Update log** | The last N `TelegramUpdate` rows: type, route chosen, status, latency, received at. Filter by status and route | None (read only) |
| **Route explainer** | Moved to [EPIC-011](EPIC-011-telegram-debugger-explain-replay.md), with **Run for real** | — |
| **Template preview** | Pick a template and sample data: the rendered HTML, the escaping applied, the button layout, and each button's callback data with its byte size (limit 64) | None |
| **Callback decoder** | Paste callback data: valid, tampered or expired, and the action it decodes to | None |
| **Policy explainer** | For a category and a time: would a message be sent now, deferred, capped or grouped, and why (needs EPIC-010) | None |
| **Send test message** | Send a chosen template to the admin's own chat through `service.reply`: immediately, no queue, no policy | One real message, to the allowlisted chat only |
| **Session peek** | The current pending mode and its remaining TTL, with a **Clear** button | Clear deletes that one session key |
| **Health** | Webhook status, queue depth, last successful send, error rate (reuses `GET /integrations/telegram/status`, BE-043) | None |

**Rules**

- **Dry run by default.** Only *Send test message* and *Clear session* change anything, and each asks for confirmation (*Run for real*: EPIC-011).
- **Test messages go only to the allowlisted chat**, through the normal sender, with a low rate limit (10 per hour). They are immediate: quiet hours do not apply to a message the admin just asked for.
- **No message content from real traffic.** The update log shows metadata only, as the logs already do (5.6). Composed text exists only in the request and is not stored or logged.
- **No secrets on screen:** never the bot token, the webhook secret, the HMAC key or an API key. Signatures are shown as valid or invalid, not as values.
- **Every playground action is recorded** (who, which tool, when, outcome), without content.

**States to polish (web):** loading, empty (no updates yet), error, the "playground is off" state, the not-an-admin state, the confirmation dialogs, phone width, light and dark, keyboard use. It follows `DESIGN.md`; it is an internal tool but not an unstyled one.

## 6. Data model (draft)

| Entity | Key fields |
|---|---|
| `TelegramUpdate` | updateId (unique), chatId, messageId?, type, route, status (`processed`/`ignored`/`failed`), receivedAt |
| `TelegramSession` (Redis, TTL) | chatId, pendingMode (`vault`/`expense`/…), context, expiresAt |
| `Admin` (code only, from env for now) | userId (Clerk `sub`) |
| `PlaygroundAction` | id, adminUserId, tool, outcome, createdAt. No content |

## 7. Security and privacy

- Secret-token webhook validation, a user-ID allowlist, signed callback data, and rate limits on the webhook.
- Bot tokens and n8n secrets only in env and credential stores. Rotation is documented (BotFather `/revoke`).
- Minimal content in messages:
  - titles and dates by default;
  - amounts and personal details only where enabled;
  - **never** document numbers or child support evidence.
- Media is processed server-side and retained only per feature policy. No message text in logs.
- **Playground (5.7):** admin-only through one shared dependency (`require_admin`); machines are never admins; off by default and never in production; dry run by default; test messages only to the allowlisted chat; no real message content, no secrets on screen; every action recorded. Each playground endpoint has tests for: no credentials (`401`), a signed-in non-admin (`403`), a valid API key (`403`), and the playground switched off (`404`).

## 8. Epic acceptance criteria

- [ ] Only my account gets responses. Messages from others are ignored and counted.
- [ ] Duplicate deliveries (same `update_id`) never cause duplicate records.
- [ ] Text, voice, photo, document, every listed command and every callback button route to the correct feature, covered by router tests with recorded payloads.
- [ ] All outbound messages go through the Telegram service (`service.reply` here; `service.send` and its policies in EPIC-010).
- [ ] Tampered or expired callback buttons are rejected.
- [ ] Dev and prod bots are separate; `make telegram-webhook` and `make telegram-info` work locally through a tunnel.
- [ ] AI work runs async, so the user sees "Working on it…" immediately, then the result.
- [ ] Playground: only an admin can open it or call its endpoints; a non-admin user and a machine get `403`; with the switch off the endpoints return `404`.
- [ ] Playground: the app refuses to start with the playground switched on in production.
- [ ] Playground: a test message reaches only the admin's own chat, and the action appears in the playground action record.
- [ ] Playground: no bot token, secret, key or real message text is visible anywhere on the screen or in its API responses.

## 9. Ticket breakdown

53 tickets (42 backend, 11 frontend) after the split, in build order within each group. Each is one reviewable change. Blocked tickets wait on the dependency named in their Status line. BE-033 needs the F-6 tickets (BE-050, BE-051), listed in `Epics/README.md`. Policy and outbox tickets (BE-024 to BE-032, BE-034, BE-043, FE-003 to FE-007) are in EPIC-010; explain and replay (BE-072 to BE-076, FE-025, FE-026, FE-030) in EPIC-011.

**Start anywhere here (no dependencies):** BE-004, BE-005, BE-010, BE-018, BE-020, BE-036, FE-002.

### Inbound: webhook, allowlist, idempotency, router

- [BE-004](../tickets/backend/BE-004-telegram-settings.md): Telegram settings (bot token, webhook secret, allowed user ID). Depends on: none
- [BE-005](../tickets/backend/BE-005-aiogram-and-update-fixtures.md): Add aiogram and parse recorded update payloads. Depends on: none
- [BE-006](../tickets/backend/BE-006-inbound-update-mapping.md): Map aiogram's Update to our own InboundUpdate. Depends on: BE-005
- [BE-007](../tickets/backend/BE-007-telegram-secret-guard.md): Webhook guard: require_telegram_secret dependency. Depends on: BE-004
- [BE-008](../tickets/backend/BE-008-telegram-webhook-route.md): Webhook route that accepts and parses updates. Depends on: BE-006, BE-007
- [BE-009](../tickets/backend/BE-009-telegram-allowlist.md): Allowlist: only the owner's updates are processed. Depends on: BE-008
- [BE-010](../tickets/backend/BE-010-telegram-update-model.md): TelegramUpdate table and migration. Depends on: none
- [BE-011](../tickets/backend/BE-011-telegram-update-repository.md): Repository: claim an update once, mark its outcome. Depends on: BE-006, BE-010
- [BE-012](../tickets/backend/BE-012-webhook-idempotency.md): Webhook processes each update once. Depends on: BE-009, BE-011
- [BE-013](../tickets/backend/BE-013-update-router-core.md): Router: callback, command and default routes. Depends on: BE-006
- [BE-014](../tickets/backend/BE-014-update-router-keywords.md): Router: caption keywords. Depends on: BE-013
- [BE-015](../tickets/backend/BE-015-handler-registry-dispatch.md): Handler registry and dispatch from the webhook. Depends on: BE-012, BE-013
- [BE-016](../tickets/backend/BE-016-session-store-pending-mode.md): Session store port and pending mode in the router. Depends on: BE-015
- [BE-017](../tickets/backend/BE-017-redis-session-store.md): Redis client and Redis-backed session store. Depends on: BE-016

### Outbound: sender, templates, buttons

- [BE-018](../tickets/backend/BE-018-telegram-sender-port.md): Sender port and a recording fake. Depends on: none
- [BE-019](../tickets/backend/BE-019-aiogram-sender-adapter.md): aiogram Bot adapter for the sender port. Depends on: BE-004, BE-005, BE-018
- [BE-020](../tickets/backend/BE-020-message-templates.md): Message templates with central HTML escaping. Depends on: none
- [BE-021](../tickets/backend/BE-021-help-reply-end-to-end.md): The bot replies: /help works end to end. Depends on: BE-015, BE-019, BE-020
- [BE-022](../tickets/backend/BE-022-signed-callback-data.md): Signed callback data (HMAC) for inline buttons. Depends on: BE-004
- [BE-023](../tickets/backend/BE-023-inline-buttons-and-callback-verification.md): Inline buttons and verified button taps. Depends on: BE-021, BE-022
- [BE-033](../tickets/backend/BE-033-working-on-it-edit.md): "Working on it…" then edit: service edit and delete. Depends on: BE-021, BE-050, BE-051

### Media and n8n

- [BE-035](../tickets/backend/BE-035-media-download-limits.md): Download media with size and type limits. Depends on: BE-019
- [BE-045](../tickets/backend/BE-045-keep-or-discard-media-prompt.md): Ask "Keep this file?" after media is processed. Depends on: BE-017, BE-023, BE-035
- [BE-036](../tickets/backend/BE-036-n8n-response-schemas.md): Strict schemas for n8n transcribe and OCR responses. Depends on: none
- [BE-037](../tickets/backend/BE-037-n8n-client-port.md): n8n client port and fake. Depends on: BE-036
- [BE-038](../tickets/backend/BE-038-n8n-httpx-client-hmac.md): n8n httpx client with HMAC-signed requests. Depends on: BE-037
- [BE-041](../tickets/backend/BE-041-n8n-workflows-folder-schemas.md): integrations/n8n: exported schemas and workflow folder. Depends on: BE-036

### Ops, observability, security

- [BE-039](../tickets/backend/BE-039-make-telegram-webhook-info.md): make telegram-webhook and make telegram-info. Depends on: BE-004, BE-005
- [BE-040](../tickets/backend/BE-040-bot-setup-runbook-commands.md): Bot setup runbook and command list script. Depends on: BE-013, BE-039
- [BE-042](../tickets/backend/BE-042-structured-webhook-logs.md): Structured logs for the webhook (never message text). Depends on: BE-015
- [BE-044](../tickets/backend/BE-044-webhook-rate-limit.md): Rate limit on the webhook. Depends on: BE-008
- [BE-046](../tickets/backend/BE-046-start-code-pairing.md): Pair the bot with a one-time /start code — **blocked**. Depends on: BE-009, BE-021, F-1

### Frontend

- [FE-002](../tickets/frontend/FE-002-extract-shared-api-request.md): Extract the shared API request helper (no behaviour change). Depends on: none

### Debugger playground (5.7)

20 tickets (10 backend, 10 frontend) for the first slice: update log, template preview, send test message.

**Start here (dependencies already merged):** BE-065 and BE-069, then BE-066 to BE-068. FE-018 follows BE-067, then FE-019 and FE-020. Everything else waits on the Telegram tickets named in its `Depends on` line.

**Human step:** set `ADMIN_USER_IDS` (your Clerk user ID) and `TELEGRAM_PLAYGROUND_ENABLED=true` in `api/.env` for development.

Backend:

- [BE-065](../tickets/backend/BE-065-admin-settings.md): Admin settings: `ADMIN_USER_IDS` and the pure `is_admin`. Depends on: none
- [BE-066](../tickets/backend/BE-066-require-admin-dependency.md): `require_admin`: the shared admin-only dependency. Depends on: BE-065
- [BE-067](../tickets/backend/BE-067-me-roles.md): `GET /me` returns `roles`. Depends on: BE-065
- [BE-068](../tickets/backend/BE-068-playground-switch-and-router.md): Playground switch, `APP_ENV`, and the guarded `/admin/telegram` router. Depends on: BE-066
- [BE-069](../tickets/backend/BE-069-playground-actions-table.md): `playground_actions` table and its two repository functions. Depends on: none
- [BE-070](../tickets/backend/BE-070-list-recent-updates-repository.md): Repository: list recent Telegram updates with filters. Depends on: BE-011
- [BE-071](../tickets/backend/BE-071-playground-updates-endpoint.md): `GET /admin/telegram/updates`: the update log. Depends on: BE-068, BE-069, BE-070
- [BE-077](../tickets/backend/BE-077-template-catalog.md): Template catalog: names and required fields (pure). Depends on: BE-020
- [BE-078](../tickets/backend/BE-078-playground-templates-endpoints.md): `GET /admin/telegram/templates` and `POST …/templates/preview`. Depends on: BE-068, BE-069, BE-077
- [BE-079](../tickets/backend/BE-079-playground-test-message-endpoint.md): `POST /admin/telegram/test-message`: send a test to the owner's chat now. Depends on: BE-021, BE-068, BE-069, BE-077

Frontend:

- [FE-018](../tickets/frontend/FE-018-session-roles.md): Session roles: `/me` client, `isAdmin` and a small store. Depends on: BE-067
- [FE-019](../tickets/frontend/FE-019-screen-switch-admin-entry.md): Screen switch from the URL hash, and an admin-only rail entry. Depends on: FE-018
- [FE-020](../tickets/frontend/FE-020-playground-shell.md): Playground shell: tabs and the 'off' and 'not an admin' states. Depends on: FE-019
- [FE-021](../tickets/frontend/FE-021-playground-client-read.md): Playground client, part 1: probe, updates, templates; connect the gate. Depends on: FE-020, BE-068, BE-071, BE-078
- [FE-022](../tickets/frontend/FE-022-playground-client-actions.md): Playground client, part 2: send test message. Depends on: FE-021, BE-079
- [FE-023](../tickets/frontend/FE-023-update-log-panel.md): Update log panel (presentational, all states). Depends on: FE-020
- [FE-024](../tickets/frontend/FE-024-wire-update-log.md): Wire the update log to the API. Depends on: FE-021, FE-023
- [FE-027](../tickets/frontend/FE-027-template-preview-panel.md): Template preview panel (presentational, all states). Depends on: FE-020
- [FE-028](../tickets/frontend/FE-028-wire-template-preview.md): Wire the template preview to the API. Depends on: FE-021, FE-027
- [FE-029](../tickets/frontend/FE-029-send-test-message.md): Send test message: panel, confirmation and wiring. Depends on: FE-021, FE-022, FE-028

Not ticketed yet (later tools): callback decoder (with composing callback taps and button preview), policy explainer (after EPIC-010), session peek, health, a screen for the action record, an admins table.

### Not ticketed here

- Feature commands (`/now`, `/inbox`, `/radar`, `/vault`, …): each owning epic registers its handler in `HANDLERS` (BE-015). Until then they answer "That isn't available yet."
- n8n contracts for `parse_dump`, `parse_expense`, `extract_document`: EPIC-003, EPIC-002, EPIC-006.
- Alerting on failures (§5.6) and scheduled clean-up of old updates: F-6.
- Production hosting for the webhook: undecided; only the ngrok dev set-up is covered.
- Spanish templates: replies are English only for now.

## 10. Open questions (answer in place)

1. Architecture: A (n8n-first) or B (API-first)?
   - Answer: API-first
2. Where is the API reachable over public HTTPS for the webhook (tunnel, VPS, cloud)?
   - Answer: ngrok tunnel
3. Your Telegram user ID (or should the bot capture it on a one-time `/start <code>` pairing)?
   - Answer: one-time /start code pairing (deferred for further investigation)
   - (assumed) Until pairing is designed (BE-046), the ID comes from `TELEGRAM_ALLOWED_USER_ID`.
4. Bot reply language: Spanish, English, or mirror the message?
   - Answer: English
5. Default quiet hours, and which categories may break through them (e.g. "due today" bills)? (now EPIC-010)
   - Answer: Quiet hours 20:00 - 8:00
   - (assumed) No category breaks through quiet hours by default; `urgentCategories` is configurable (BE-024, BE-027).
6. Should important notifications fall back to email when Telegram fails?
   - Answer: Yes (deferred)
7. Keep voice notes and photos after parsing, or discard them by default?
   - Answer: Ask whether to keep (always)
   - (assumed) An unanswered prompt discards after 24 hours; nothing is stored before a Keep (BE-045).
8. Playground: how is an admin identified? By Clerk user ID in an environment variable (`ADMIN_USER_IDS`; recommended, matches `CLERK_ALLOWED_USER_IDS`, needs nothing new from Clerk), or by email (needs the email added to Clerk's session token as a custom claim, and a verified-email check)?
   - Answer: By Clerk user ID, in `ADMIN_USER_IDS` in `api/.env`.
9. Playground: will there be more admins than the owner? If yes, is an environment list enough, or do you want an admins table with a screen to add and remove them?
   - Answer: Yes, more admins are expected.
   - (assumed) The environment list is enough for now; an admins table with a screen is a later decision.
10. Playground: available in production, or development only? (The switch `TELEGRAM_PLAYGROUND_ENABLED` covers both; this decides its production default.)
   - Answer: No. Development only.
   - (assumed) Enforced by refusing to start when the switch is on in production; how the app knows it is in production (for example an `APP_ENV` setting) is decided when unfolding.
11. Playground (now EPIC-011): may the route explainer ever *execute* the handler (a real end-to-end replay), or stay dry run only? Recommended: dry run only; real tests go through the dev bot.
   - Answer: Yes, as an explicit, confirmed *Run for real* mode. Dry run stays the default.
12. Playground: which tools first? Recommended first slice: update log, route explainer, template preview. Then send test message, then the rest.
   - Answer: Update log, route explainer, template preview, send test message.
