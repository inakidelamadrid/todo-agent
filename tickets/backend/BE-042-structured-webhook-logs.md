# BE-042: Structured logs for the webhook (never message text)

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.6, §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-015
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 4 files, ~10 min

## Goal

Each handled update produces one structured log line with its type, route, outcome and latency, and no message content.

## Why this ticket exists

When the bot misbehaves, the log should answer "what arrived, where did it go, how long did it take". Privacy is the constraint: text, captions and button data must never be logged, and a test enforces it.

## Read first

- https://www.structlog.org/en/stable/getting-started.html and `structlog.testing.capture_logs`.
- `api/app/telegram/webhook.py`: the existing `logger` calls from BE-008, BE-009, BE-015.

## Design

- **Pattern:** Logging at the edge: handlers and pure functions do not log; the webhook logs once per update.
- **Data flow:** webhook → `log.info("telegram.update", …fields)` at the end of each path.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `structlog` | **new** | Key-value (JSON) logging | 26.1.0, MIT OR Apache-2.0, released 2026-06-06, Python ≥3.10. The standard structured-logging library; ships a test helper to assert on log events. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add structlog`.
- `api/app/logging.py` (new): `configure_logging()` (JSON renderer, ISO timestamps, level from `LOG_LEVEL`, default `INFO`), called in `create_app`.
- `api/app/telegram/webhook.py` (changed): replace the stdlib logger calls.
- `api/tests/test_telegram_logging.py` (new).

**Events**

| Event | Fields |
|---|---|
| `telegram.update` | `update_id`, `kind`, `route`, `outcome` (`processed`, `duplicate`, `failed`, `rejected_callback`), `latency_ms` |
| `telegram.ignored` | none (a counter; no IDs) |
| `telegram.unparseable` | none |
| `telegram.handler_failed`, `telegram.reply_failed` | `update_id`, `route`, `error_type` (the exception class name only) |

**Never logged:** `text`, `caption`, `callback_data`, `command_args`, `user_id`, `chat_id`, file IDs, tokens, secrets.

## Steps

1. Check `structlog` on PyPI again; add it.
2. `configure_logging`.
3. Replace the log calls; add latency timing.
4. Tests.

## Tests

- `test_processed_update_logs_one_event_with_fields`
- `test_duplicate_logs_outcome_duplicate`
- `test_ignored_update_logs_no_ids`
- `test_no_log_event_contains_message_content`: post every fixture, then assert no captured event contains the fixture's text, caption, callback data or any user ID.
- `test_handler_failure_logs_error_type_only`

## Acceptance criteria

- [ ] One `telegram.update` event per processed update
- [ ] The content test passes for all seven fixtures
- [ ] No stdlib `logging` calls remain in `api/app/telegram/`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Run `make api-dev`, send a message to the dev bot, and read the JSON line in the terminal: it has a route and a latency and none of your words.

## Review guide

Read the diff in this order, and check:

1. The fields table against the code.
2. The content test: is its list of forbidden values complete?

Things that should *not* be in the diff: metrics backends, alerting, log shipping.

## Out of scope

- Health and counts over HTTP → BE-043.
- Alerting → BE-057.

## Notes / log

The agent adds progress notes, decisions and open questions here.
