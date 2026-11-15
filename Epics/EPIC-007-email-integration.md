# EPIC-007: Email integration (infra)

- **Status:** draft
- **Type:** infrastructure
- **Owner:** Ignacio
- **Depends on:** F-1 User login, F-2 Scoped API keys, F-6 Scheduler & notifications (queue on the existing Redis)
- **Used by:**
  - EPIC-001: signing requests to the ex-spouse, reminders, dispute alerts, lawyer pack delivery;
  - EPIC-003: an inbound forward-to-inbox address;
  - EPIC-002: forwarded receipts become expense candidates;
  - EPIC-004: an email fallback for radar reminders;
  - EPIC-005: an optional weekly summary by email;
  - EPIC-006: forwarded documents go to the vault confirm flow.

## 1. Summary

A shared, reliable email capability for the whole app:

1. **Outbound:**
   - transactional emails sent from my own domain through a provider;
   - templated (ES/EN), queued, retried and tracked (delivered, bounced, complained);
   - with per-category preferences and unsubscribe.
2. **Inbound:**
   - a private address (e.g. `inbox@<my-domain>`) that receives forwarded emails;
   - verifies the sender;
   - routes the content and attachments to the right feature: brain dump, expense, vault or child support evidence.
3. **Local dev:** a fake SMTP inbox (Mailpit) in `docker-compose`, so no real email is ever sent from development.

## 2. Goals

- Emails land in the inbox, not spam: SPF, DKIM and DMARC are aligned on my domain.
- No feature talks to the provider directly. Every feature calls one `send_email(template, to, data, category)` service.
- No lost or duplicate emails: a queue, idempotency keys and retries with backoff.
- People other than me (e.g. the ex-spouse) get clean, respectful, minimal emails with no tracking pixels.
- Forwarding an email to the app is as easy as sending a Telegram message.

## 3. Non-goals

- A full email client or reading my personal mailbox (no Gmail inbox scopes).
- Marketing or bulk email.
- Open or click tracking pixels: off by design.

## 4. Requirements

### 4.1 Provider and domain
- **Provider:** pick one with good deliverability, an inbound parse webhook and a sandbox, e.g. **Resend**, **Postmark** or **Amazon SES** (decision in the open questions).
- **Sending domain:** a subdomain such as `mail.<my-domain>`, with SPF, DKIM and DMARC (`p=quarantine` once stable), plus an optional custom return-path.
- **From addresses:**
  - `todo-agent <no-reply@mail.<domain>>` for notifications;
  - a reply-to address only where replies matter (EPIC-001 disputes go to the app, not the void).
- The provider API key lives in the backend env (`.env`, gitignored) and is never sent to the frontend or n8n unless a flow strictly needs it.

### 4.2 Outbound service
- `EmailService.send(template_id, to, locale, data, category, idempotency_key)`:
  - enqueues a job (Redis), and a worker sends it through the provider;
  - retries with exponential backoff on 5xx or timeouts, up to N attempts; then the email is marked `failed` and an alert goes to me (Telegram, EPIC-008).
- **Templates:**
  - versioned in the repo;
  - HTML + plain text, ES/EN;
  - variables validated against a schema;
  - rendered server-side (MJML or a Python template engine; decided in a ticket);
  - styled with the design tokens (Midnight Transit, light background for email clients).
- **Categories** (each with its own preference):
  - `security` (login links; always on);
  - `signing` (EPIC-001 requests to third parties);
  - `reminders` (EPIC-004);
  - `summaries` (EPIC-005, EPIC-001 lawyer pack);
  - `system` (alerts).
- **Preferences and unsubscribe:**
  - one-click unsubscribe (`List-Unsubscribe` + `List-Unsubscribe-Post`) for non-essential categories;
  - third-party recipients (the ex-spouse) can opt out of reminders, but not out of a specific signing request they're still part of.
- **Attachments:** allowed for the lawyer pack, with a size cap. Large packs are sent as a short-lived Drive link instead.

### 4.3 Delivery events
- A provider webhook endpoint `POST /integrations/email/events` (verified signature) records `delivered`, `bounced`, `complained` and `deferred`.
- **Suppression list:** hard bounces and complaints block future sends to that address. The UI shows "Email to X is failing" where it matters, e.g. the EPIC-001 recipient.
- Each `EmailMessage` keeps its status timeline for debugging (no body stored, only the template ID and variables hash).

### 4.4 Inbound email
- **Address:** `inbox@mail.<domain>`, or a plus-addressed variant per purpose:
  - `inbox+dump@` → EPIC-003 brain dump;
  - `inbox+expense@` → EPIC-002;
  - `inbox+vault@` → EPIC-006;
  - `inbox+support@` → EPIC-001 evidence.
- **Flow:**
  1. The provider's inbound webhook posts to `POST /integrations/email/inbound` (signature verified).
  2. **Sender allowlist:** only my addresses are accepted. Anything else is dropped and logged, never processed.
  3. SPF/DKIM results are checked (reject on fail).
  4. The body is turned into text (HTML stripped, quotes and signatures trimmed). Attachments go to F-4 storage (Drive) with hashes.
  5. The item routes to the target feature's intake (the same intake n8n/Telegram uses), creating **Inbox items to confirm**, never final records.
  6. A confirmation reply goes out by email (or Telegram), e.g. "Got it: 2 items in your inbox".
- **Idempotency:** on the provider message ID.

### 4.5 Local development
- **Mailpit** service in `docker-compose.yml` (SMTP + web UI on `127.0.0.1` only).
- `EMAIL_TRANSPORT=smtp-dev` sends every outbound email to Mailpit.
- `make mail-ui` opens the Mailpit UI.
- **Tests:** a fake transport captures messages, and inbound is tested with recorded provider payloads.

## 5. Data model (draft)

| Entity | Key fields |
|---|---|
| `EmailMessage` | id, templateId, templateVersion, toHash (+ masked display), category, locale, status (`queued`/`sent`/`delivered`/`bounced`/`complained`/`failed`), providerMessageId?, idempotencyKey, attempts, lastError?, createdAt |
| `EmailEvent` | messageId, type, at, raw (minimal) |
| `EmailSuppression` | addressHash, reason, at |
| `EmailPreference` | addressHash or userId, category, enabled |
| `InboundEmail` | id, providerMessageId, fromHash, purpose, receivedAt, status (`accepted`/`rejected`), reason?, createdItemIds[] |

## 6. Security and privacy

- Every webhook (events, inbound) verifies the provider signature and has a rate limit. Both are public endpoints, guarded by the signature and an allowlist.
- No email bodies are stored. Recipient addresses are hashed in logs. Third-party contact data (the ex-spouse) is minimal and deletable.
- Inbound attachments are scanned for type and size before storing. Executables are never accepted.
- Login links sent by email (F-1) are single-use, short-lived, and tied to the device or browser where possible.

## 7. Epic acceptance criteria

- [ ] Emails from the app pass SPF, DKIM and DMARC, and land in Gmail and Outlook inboxes (tested).
- [ ] Features send only through `EmailService`. Retries, idempotency and failure alerts work.
- [ ] Bounces and complaints update the status and suppress future sends, and the UI surfaces failing recipients.
- [ ] Unsubscribe works for non-essential categories and is respected immediately.
- [ ] Forwarding an email (with attachments) to the inbound address from an allowed sender creates Inbox items in the right feature. Unknown senders are rejected.
- [ ] Development never sends real email: Mailpit captures everything locally.

## 8. Proposed ticket breakdown (draft)

- **Backend:**
  - `EmailService` + queue worker + provider adapter.
  - Templates system (ES/EN) + first templates (login link, signing request, reminder, weekly summary).
  - Delivery events webhook + suppression.
  - Preferences + unsubscribe.
  - Inbound webhook + allowlist + routing to intakes.
- **Ops:**
  - Domain DNS (SPF, DKIM, DMARC), provider setup.
  - Mailpit in `docker-compose` + `make mail-ui`.
- **Frontend:** notification and email preferences UI; "email failing" indicators.

## 9. Open questions (answer in place)

1. Which provider: Resend, Postmark, SES or other?
   - Answer:
2. Which domain or subdomain will send email? Do you control its DNS?
   - Answer:
3. Inbound email: yes for the MVP? Which purposes (dump, expense, vault, support)?
   - Answer:
4. Which of your addresses are allowed senders?
   - Answer:
5. Template languages: Spanish, English or both (per recipient)?
   - Answer:
6. Should failure alerts go to Telegram, email or both?
   - Answer:
