# BE-029: Outbound message table and enqueue

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-010 (for the models module)
- **Can run in parallel with:** BE-018 to BE-028
- **Public endpoint?** no
- **Review size:** ~110 lines, 3 files + generated migration, ~15 min

## Goal

Messages the app wants to send are stored as rows first; storing the same idempotency key twice yields one row.

## Why this ticket exists

This is the outbox: the intent to send is saved in the same database as the data that caused it, so a crash between "decided to remind" and "sent" loses nothing, and a retried job cannot send twice. Sending itself comes later (BE-031).

## Read first

- `api/app/telegram/models.py`, `repository.py` (BE-010, BE-011).
- The outbox idea: write a row describing the message; a separate worker delivers rows and marks them sent.

## Design

- **Pattern:** Outbox + idempotent insert. Each row is a command: a frozen description of an action to perform later.
- **Data flow:** feature → `enqueue(session, NewOutbound)` → row (`queued` or `deferred`).

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/models.py` (changed): `TelegramOutbound`. Generated revision `create telegram_outbound`.
- `api/app/telegram/repository.py` (changed).
- `api/tests/test_telegram_outbound_repository.py` (new).

**Table `telegram_outbound`**

| Column | Type | Rules |
|---|---|---|
| `id` | UUID | primary key |
| `chat_id` | `BigInteger` | not null |
| `template` | `String(40)` | not null |
| `data` | `JSONB` | object of string → string |
| `buttons` | `JSONB` | rows of `{text, action, arg}`; default `[]` |
| `category` | `String(30)` | not null |
| `status` | `String(10)` | CHECK: `queued`, `deferred`, `sent`, `failed` |
| `idempotency_key` | `String(120)` | **unique**, not null |
| `scheduled_for` | timestamptz | not null |
| `attempts` | `SmallInteger` | default 0 |
| `telegram_message_id` | `BigInteger` | nullable |
| `created_at`, `sent_at` | timestamptz | `sent_at` nullable |

Index on `(status, scheduled_for)`. The row stores the template name and data, not rendered text, so message content at rest is minimal.

**Functions**

- `NewOutbound`: frozen model with `chat_id, template, data, buttons, category, idempotency_key, status, scheduled_for`.
- `async def enqueue(session, new: NewOutbound) -> tuple[TelegramOutbound, bool]`: insert with `ON CONFLICT (idempotency_key) DO NOTHING`; returns the stored row and whether it was created now.
- `async def count_sent_since(session, category: str, since: datetime) -> int`: rows with `status = 'sent'` and `sent_at >= since`. Feeds the cap in BE-025.

## Steps

1. Model and migration.
2. `enqueue`.
3. `count_sent_since`.
4. Tests.

## Tests

- `test_enqueue_creates_row`
- `test_enqueue_same_key_returns_existing_and_false`
- `test_concurrent_enqueue_same_key_creates_one_row`
- `test_status_check_rejects_unknown`
- `test_count_sent_since_counts_only_sent_in_category`

## Acceptance criteria

- [ ] `idempotency_key` is unique at the database level
- [ ] Rendered message text is not stored
- [ ] `downgrade` removes the table
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-migrate
```

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The table against §6 of the epic.
2. `enqueue`: one statement; the conflict path returns the existing row.
3. What is stored: could a database dump reveal message text? (Only template data.)

Things that should *not* be in the diff: sending, policy decisions, a worker.

## Out of scope

- Deciding status and time → BE-030.
- Delivery → BE-031.

## Notes / log

The agent adds progress notes, decisions and open questions here.
