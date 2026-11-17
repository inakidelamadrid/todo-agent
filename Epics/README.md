# Epics

Epics are feature-level requirements, polished by the human before they become work. When an epic is ready, it gets broken into `tickets/backend/BE-…` and `tickets/frontend/FE-…` tickets. Each ticket links back to its epic.

## Feature epics

| Epic | Status | Summary |
|---|---|---|
| [EPIC-001: Child support records](EPIC-001-child-support-records.md) | draft | Monthly child support payments with proof, the ex-spouse's digital acknowledgment, Google Drive filing and lawyer-ready summaries |
| [EPIC-002: Expense tracking via Telegram](EPIC-002-expense-tracking-telegram.md) | draft | Log expenses by Telegram (text, photo, voice) through n8n into the API, with category/month/year heat maps |
| [EPIC-003: Brain-dump inbox + "What now?"](EPIC-003-brain-dump-inbox-what-now.md) | draft | Capture anything (Telegram/web), AI splits it into tasks/notes/expenses for quick triage, and one-tap "What now?" picks a single task with its first step and a focus timer |
| [EPIC-004: Deadline radar](EPIC-004-deadline-radar.md) | draft | One view of everything dated in the next 14 days (bills, child support, tasks, documents, appointments), with one-tap actions and grouped, capped reminders |
| [EPIC-005: Scheduled weekly reset](EPIC-005-weekly-reset.md) | draft | A guided 15-minute, 5-step weekly session (wins, inbox, look ahead, Big 3, money), invited by Telegram, ending in a 5-line summary |
| [EPIC-006: Documents vault](EPIC-006-documents-vault.md) | draft | An index of important documents stored in Drive, with AI field extraction, masked numbers, renewal checklists and expiry on the radar |

## Infrastructure epics

| Epic | Status | Summary |
|---|---|---|
| [EPIC-007: Email integration](EPIC-007-email-integration.md) | draft | Outbound transactional email (domain auth, templates, queue, bounces, unsubscribe), inbound forward-to-app routing, Mailpit for dev |
| [EPIC-008: Telegram integration](EPIC-008-telegram-integration.md) | in-tickets | One private bot: verified webhook, allowlist, idempotency, router to features, central outbound service with quiet hours/caps, the n8n AI contract, dev/prod bots, and an admin-only debugger playground (5.7, not unfolded yet) |
| [EPIC-009: User login with Clerk](EPIC-009-user-login-clerk.md) | in-tickets | Sign-in for the owner with Clerk: sign-in screen in the web app, verified session tokens in the API, API keys kept for machines, owner-only allowlist |

## Lifecycle

`draft` → `ready` (open questions answered) → `in-tickets` (broken down) → `done`

## Shared foundations

Several epics need these. Build them first, as their own tickets.

| Foundation | Why | Needed by |
|---|---|---|
| **F-1 User login** | Personal and sensitive data, plus a second person (EPIC-001). The API key covers machines, not people. Session login for me (passkey or email magic link), with step-up re-auth for sensitive actions. Delivered by **EPIC-009** (Clerk; ngrok's auth was evaluated and rejected). | 001–006 |
| **F-2 Scoped API keys** | Separate, revocable keys per integration (`web-proxy`, `n8n-telegram`, …), each with a label and scopes such as `expenses:write` or `inbox:write`. | 002, 003, 007, 008 |
| **F-3 Google Drive integration** | OAuth with the `drive.file` scope (the app only sees files it created), a root folder, and an upload/link service. The database stores only file IDs and hashes. | 001, 002 (receipts), 006 |
| **F-4 File storage and hashing** | SHA-256 of every stored document, so later tampering can be detected. | 001, 002, 006, 007 (inbound attachments) |
| **F-5 AI service** | Summaries, parsing, ranking and extraction, grounded only in my data, with strict output schemas and minimal data sent to the provider. | 001, 002, 003, 005, 006 |
| **F-6 Scheduler & notifications** | Scheduled jobs and a queue (Redis): reminders, invites, digests. One notification policy (quiet hours, pause, caps, grouping) for every channel. | 001, 003, 004, 005, 007, 008 |
| **F-7 Telegram channel** | Delivered by **EPIC-008**. | 002, 003, 004, 005, 006 |
| **F-8 Email channel** | Delivered by **EPIC-007**. | 001, 003, 004, 005, 006 |

## F-6 tickets

F-6 has no epic file; this list is its breakdown. The job runner is **taskiq** with a Redis broker (arq was rejected: maintenance-only, and it pins the Redis client below version 6). Features call only the `JobQueue` port and add lines to the `JOBS` registry and the `SCHEDULES` table.

The notification policy half of F-6 (quiet hours, pause, caps, grouping) is ticketed under EPIC-008 as BE-024 to BE-027.

- [BE-047](../tickets/backend/BE-047-job-queue-port.md): Job queue port, job registry and an inline fake. Depends on: none
- [BE-048](../tickets/backend/BE-048-add-taskiq-in-memory.md): Add taskiq and run a ping job in memory. Depends on: BE-047
- [BE-049](../tickets/backend/BE-049-taskiq-redis-worker.md): Redis broker and the worker process (make worker-dev). Depends on: BE-017, BE-048
- [BE-050](../tickets/backend/BE-050-taskiq-job-queue-adapter.md): JobQueue adapter: enqueue once, optionally later. Depends on: BE-049
- [BE-051](../tickets/backend/BE-051-job-context-session-sender.md): Give jobs a database session and the Telegram sender. Depends on: BE-049, BE-019
- [BE-052](../tickets/backend/BE-052-periodic-schedules-heartbeat.md): Periodic schedules table, scheduler process and heartbeat. Depends on: BE-050, BE-051
- [BE-053](../tickets/backend/BE-053-job-retry-rules.md): Retry rules for failed jobs. Depends on: BE-051
- [BE-054](../tickets/backend/BE-054-job-failures-table.md): Record jobs that failed for good. Depends on: BE-053
- [BE-055](../tickets/backend/BE-055-daily-cleanup-job.md): Daily clean-up job. Depends on: BE-052, BE-054, BE-011
- [BE-056](../tickets/backend/BE-056-jobs-status-endpoint.md): GET /jobs/status. Depends on: BE-052, BE-054
- [BE-057](../tickets/backend/BE-057-job-failure-alert.md): Tell the owner when a job fails for good. Depends on: BE-054, BE-030, BE-031
- [FE-008](../tickets/frontend/FE-008-worker-status-line.md): Background worker status line in the settings sheet. Depends on: BE-056, FE-007

Unblocks BE-031 to BE-033 (Telegram delivery). Running the worker and scheduler in production is undecided, along with hosting.

## Suggested order

1. **Foundations:** F-1 login (EPIC-009), F-2 scoped keys, F-6 scheduler, then EPIC-008 Telegram and EPIC-007 Email (outbound first).
2. **EPIC-004 Deadline radar** (bills + appointments adapters): quick win on existing data.
3. **EPIC-003 Brain dump + What now?:** introduces Tasks, which EPIC-004 and EPIC-005 use.
4. **EPIC-002 Expenses** and **EPIC-006 Documents vault** (needs F-3 Drive and F-4).
5. **EPIC-005 Weekly reset:** ties everything together.
6. **EPIC-001 Child support:** the most legal and privacy sensitive; after login, Drive and email are proven.

## Conventions

- Money is integer cents with a per-record currency (`MXN` / `USD`). Amounts are never converted unless a feature says so explicitly. See `CLAUDE.md`.
- JSON is camelCase on the wire. Months are `YYYY-MM`. Dates are `YYYY-MM-DD`. The default timezone is America/Mexico_City.
- Secure first: every endpoint requires auth unless the epic explicitly marks it public. Public endpoints (signing page, webhooks) must be token-, signature- or allowlist-guarded.
- ADHD-friendly by default: low-friction capture, one clear next action, no guilt mechanics (no streaks, calm "past its date" language), quiet hours respected everywhere.
- Fill in each **Open questions** section in place; the "Answer:" lines are there for you.
