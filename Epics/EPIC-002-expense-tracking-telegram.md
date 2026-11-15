# EPIC-002: Expense tracking via Telegram, with heat maps

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:** F-1 User login (web), F-2 Scoped API keys (n8n), F-3 Google Drive (optional receipt storage), F-5 AI summaries (optional weekly digest). See `Epics/README.md`.
- **Related:** the bills view (bill payments count as spending), EPIC-001 (child support as a category).

## 1. Summary

Log everyday expenses by sending a **Telegram message**: text, a receipt photo or a voice note. An **n8n** workflow parses the message with AI, sends the structured expense to the API, and replies with a confirmation I can correct right there. In the web app, I review spending with **heat maps**: category × month, a day-by-day year calendar, and year-over-year.

## 2. Goals

- Logging an expense takes under 10 seconds, from my phone, in natural language.
- Parsing is accurate enough that I rarely correct anything, and correcting is one tap.
- No duplicates, no lost messages.
- Visual answers to "where does my money go?" by category, month and year.
- One source of truth: the API validates and stores, while n8n is replaceable plumbing.

## 3. Non-goals (for this epic)

- Bank or card syncing (open banking).
- Multi-user, shared household expenses.
- Investment tracking or net worth.
- Converting currencies for totals (shown per currency, as in the bills view).

## 4. Channels and roles

| Actor | Role |
|---|---|
| **Me (Telegram)** | Send expenses; confirm or correct them; ask quick questions ("how much on dining this month?") |
| **Telegram bot** | The conversational front door; only answers my Telegram user ID |
| **n8n workflow** | Receives the bot update → parses (AI/OCR/STT) → calls the API → replies |
| **API** | Validates, de-duplicates, stores, and serves aggregates for the heat maps |
| **Me (web)** | Browse, edit and delete expenses; manage categories; view heat maps |

## 5. User stories

1. I text `450 uber` and an expense is created: MXN 450.00, transport, merchant Uber, today. The bot confirms in one line.
2. I text `Costco 2,380 groceries ayer` (Spanish/English mixed) and the parser understands *ayer* = yesterday.
3. I send a **receipt photo**. OCR extracts the total, merchant and date, and the photo is optionally stored in Drive.
4. I send a **voice note**: "gasté 300 en gasolina". It's transcribed and parsed.
5. The bot replies with inline buttons: **Change category · Edit amount · Undo**. Each fix is one tap.
6. When parsing is uncertain (no amount found, ambiguous currency), the bot **asks** instead of guessing.
7. Sending the same message twice (a Telegram retry) never creates two expenses.
8. In the web app I see a **category × month heat map** for the selected year and click a cell to list its expenses.
9. I see a **year calendar heat map**, day by day, to spot spending spikes.
10. I compare **year over year**, month by month.
11. Bill payments from the bills view appear in spending **without logging them again**.
12. Optionally, I get a **weekly Telegram digest**: total spent, top categories, biggest changes from last week.

## 6. Functional requirements

### 6.1 Telegram bot
- Create the bot with BotFather and keep its token in n8n credentials only.
- **Allowlist:** process only updates from my Telegram user ID and silently drop everything else.
- **Inputs:** text, photo (receipt), voice note, plus commands:
  - `/undo` removes the last expense;
  - `/today` and `/month` give quick totals;
  - `/help`.
- **Replies:** a one-line confirmation, e.g. `✓ MXN 450.00 · Transport · Uber · Nov 14`, with inline keyboard buttons for category, amount and undo.

### 6.2 n8n workflow
1. **Telegram Trigger** (webhook).
2. **Allowlist check.**
3. **Branch by type:**
   - text → AI parse;
   - photo → OCR (vision model) → AI parse;
   - voice → speech-to-text → AI parse.
4. **AI parse** to a strict JSON schema: `{amount, currency, category, merchant, note, spentAt, confidence}`.
   - Default currency MXN; default date today, in the user's timezone (America/Mexico_City).
   - The category must come from the API's category list (fetched and cached).
5. **Below the confidence threshold:** ask a clarifying question; don't call the API.
6. **`POST /expenses`** with the **n8n API key** (scope `expenses:write`) and an **idempotency key** = `telegram:<chat_id>:<message_id>`.
7. **Reply** with the confirmation and buttons. Callback buttons call `PATCH /expenses/{id}` or `DELETE /expenses/{id}`.
8. **On API error:** reply with a short message, and retry later for 5xx or network errors (no data loss).

**Hosting options:** n8n Cloud, or self-hosted (Docker next to Postgres/Redis) behind a tunnel or a reverse proxy with HTTPS. Telegram webhooks require a public HTTPS URL.

**Portability:** all business rules live in the API, so the bot can later move into FastAPI (e.g. a `/telegram/webhook`) without changing the data.

### 6.3 API: expenses
- `POST /expenses` (scoped key or user session):
  - validates the payload;
  - honours the `Idempotency-Key` header: a repeat returns the original expense;
  - returns `201`.
- `GET /expenses` with filters: `from`, `to`, `category`, `currency`, `source`, `q` (search the merchant and note), with pagination.
- `GET` / `PATCH` / `DELETE /expenses/{id}`.
- `GET /categories`, plus `POST`/`PATCH` for managing them (web only).
- **Aggregates for the heat maps (server-side, fast):**
  - `GET /spending/heatmap?year=YYYY&currency=MXN&include=bills,support` → category × month matrix.
  - `GET /spending/calendar?year=YYYY&currency=MXN` → day-by-day totals.
  - `GET /spending/yoy?years=2025,2026&currency=MXN` → monthly totals per year.
- **"Include" sources:**
  - `expenses` always;
  - `bills` (payments from the bills feature, mapped to their line as category);
  - `support` (EPIC-001 payments).
  - This avoids double logging.

### 6.4 Categories (starter set; editable)
- **Everyday:** groceries, dining, transport, fuel, health, kids, home, personal care, entertainment, shopping, travel, gifts, education, other.
- **From other features (read-only mapping):**
  - utilities, telecom, streaming and software come from bill lines;
  - child support comes from EPIC-001.
- Each category has a name, colour (from the design tokens), an icon and an `archived` flag. Renaming keeps history.

### 6.5 Heat maps (web)
1. **Category × month (primary):**
   - rows are categories, columns are Jan–Dec of the selected year;
   - cell intensity is a sequential scale of the spending amount, and empty cells stay calm;
   - the row total and column total sit on the edges;
   - hover/tap shows the exact amount and count; clicking opens a drill-down list.
2. **Year calendar:** one square per day, intensity by daily total, with week rows. Clicking a day lists that day's expenses.
3. **Year over year:** monthly totals per year as grouped columns or two lines. A heat-map strip variant is optional.
- **Controls:** year picker, currency toggle (MXN / USD, never mixed), include toggles (Bills, Child support), category filter.
- **Design:** Midnight Transit (`DESIGN.md`).
  - The intensity scale comes from the tokens, one ramp per theme, colourblind-safe and with legible contrast in light and dark.
  - Each category keeps its own colour only in legends and chips; the heat itself uses a single ramp, so cells are comparable.
- **States:** loading skeleton, an empty year ("Send your first expense to the bot"), errors with retry.
- **Mobile:** the category × month grid scrolls horizontally with a sticky category column. The calendar shows the selected month.

### 6.6 Optional: digest and budgets (later)
- Weekly digest by Telegram (F-5 summary from aggregates only).
- Monthly budgets per category, with a Telegram alert at 80% and 100%.

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `Expense` | id, amountCents, currency, categoryId, merchant, note, spentAt (`YYYY-MM-DD`), source (`telegram`/`web`/`import`), sourceRef (e.g. `telegram:<chat>:<msg>`), receiptFileId?, parseConfidence?, createdAt, updatedAt |
| `Category` | id, slug, name, colorToken, icon, kind (`expense`/`bill-line`/`support`), archived |
| `IdempotencyKey` | key (unique), expenseId, createdAt (kept N days) |
| `ApiKey` (F-2) | id, label, hashedKey, scopes[], createdAt, lastUsedAt, revokedAt |

Indexes: `(spentAt)`, `(categoryId, spentAt)`, a unique `sourceRef`.

## 8. Security and privacy

- **Bot:** a user-ID allowlist, and the bot token stays in n8n only.
- **n8n:** its own API key with scope `expenses:write` (+ `expenses:read` for quick totals), revocable on its own. No admin rights.
- **Webhook:** the secret-token header is checked (Telegram supports `secret_token`). HTTPS only.
- **Receipts:** stored in Drive (F-3), referenced by ID. OCR text is not persisted beyond what's needed.
- **AI provider:** send only the message text, image or audio needed to parse it. Never send history.
- **Rate limits:** on `POST /expenses` per key.

## 9. Epic acceptance criteria

- [ ] Text, photo and voice each create a correct expense in ≤10 s on a typical day, and the bot confirms with buttons.
- [ ] Ambiguous inputs trigger a question, not a wrong expense.
- [ ] Re-delivered Telegram updates never create duplicates (idempotency).
- [ ] Only my Telegram account can use the bot.
- [ ] The heat maps (category × month, calendar, YoY) match the database totals exactly, per currency, with include toggles working.
- [ ] Bill payments appear in spending without being logged again, and nothing is counted twice.
- [ ] Heat maps are legible in light and dark, at desktop and mobile widths.

## 10. Proposed ticket breakdown (draft)

- **Backend:**
  - BE: F-2 scoped API keys.
  - BE: expenses + categories API with idempotency.
  - BE: heat map, calendar and YoY aggregates (including bills/support sources).
  - BE (optional): Telegram webhook secret validation helper.
- **Ops:**
  - Ops: n8n hosting and HTTPS.
  - Ops: n8n workflow (text → photo → voice), exported JSON kept in `integrations/n8n/`.
- **Frontend:**
  - FE: expenses list and edit.
  - FE: category management.
  - FE: heat maps (category × month, calendar, YoY) with filters.
- **Later:** digest, budgets.

## 11. Risks

- **Parsing errors** (amounts, dates, slang). Mitigation: a strict schema, confidence threshold, one-tap fixes, and a test set of real messages.
- **n8n availability or hosting.** Mitigation: Telegram retries + idempotency, health checks, and an easy move into FastAPI.
- **AI cost and latency** for photos and voice. Mitigation: use the cheaper model for text, vision only for photos, caching.
- **Category drift.** Mitigation: a fixed list from the API, with corrections feeding a merchant → category mapping.

## 12. Open questions (answer in place)

1. Where will n8n run: n8n Cloud or self-hosted (where)?
   - Answer:
2. Which AI provider/models for text parsing, OCR and speech-to-text?
   - Answer:
3. Should receipt photos be stored (in Drive), or only the parsed data?
   - Answer:
4. Is the starter category list right? Add or remove any.
   - Answer:
5. Should the heat maps include bills and child support by default?
   - Answer:
6. Which languages for the bot replies: Spanish, English or mixed like the input?
   - Answer:
7. Default currency MXN, and how should USD be marked in messages (e.g. `usd 20`, `$20 usd`)?
   - Answer:
8. Do you want the weekly digest and/or budgets in this epic, or later?
   - Answer:
9. Should expenses be backfilled (CSV import from a bank or spreadsheet)?
   - Answer:
