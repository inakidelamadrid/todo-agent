# Epics

Epics are feature-level requirements, polished by the human before they become work. When an epic is ready, it gets broken into `tickets/backend/BE-…` and `tickets/frontend/FE-…` tickets. Each ticket links back to its epic.

| Epic | Status | Summary |
|---|---|---|
| [EPIC-001: Child support records](EPIC-001-child-support-records.md) | draft | Monthly child support payments with proof, the ex-spouse's digital acknowledgment, Google Drive filing and lawyer-ready summaries |
| [EPIC-002: Expense tracking via Telegram](EPIC-002-expense-tracking-telegram.md) | draft | Log expenses by Telegram (text, photo, voice) through n8n into the API, with category/month/year heat maps |

## Lifecycle

`draft` → `ready` (open questions answered) → `in-tickets` (broken down) → `done`

## Shared foundations

Both epics need these. Build them first, as their own tickets.

| Foundation | Why | Needed by |
|---|---|---|
| **F-1 User login** | The app becomes personal data with a second person involved. The API key alone covers machines, not people. Choose session-based login for you (passkey or email magic link), and keep scoped API keys for integrations. | 001, 002 |
| **F-2 Scoped API keys** | Separate, revocable keys per integration, e.g. `web-proxy` and `n8n-telegram`. Each key carries a label and allowed scopes, e.g. `expenses:write`. | 002 (and 001 later) |
| **F-3 Google Drive integration** | OAuth with the `drive.file` scope (the app only sees files it created), a root folder, and an upload/link service. Only file IDs and hashes are stored in the database. | 001 (receipts in 002) |
| **F-4 File storage and hashing** | SHA-256 of every stored document, so later tampering can be detected. | 001, 002 |
| **F-5 AI summaries service** | One backend service that turns structured records into short summaries. It is grounded only in your data and never invents facts. | 001, 002 |

## Conventions

- Money is integer cents with a per-record currency (`MXN` / `USD`). Amounts are never converted unless a feature says so explicitly. See `CLAUDE.md`.
- JSON is camelCase on the wire. Months are `YYYY-MM`. Dates are `YYYY-MM-DD`.
- Secure first: every endpoint requires auth unless the epic explicitly marks it public.
- Fill in each **Open questions** section in place; the "Answer:" lines are there for you.
