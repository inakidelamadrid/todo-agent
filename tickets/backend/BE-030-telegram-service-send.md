# BE-030: telegram service send(): the one function features call

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-020, BE-025, BE-026, BE-029
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~100 lines, 2 files, ~15 min

## Goal

`service.send(...)` validates a message, asks the policy when it may go out, and stores it in the outbox with that time.

## Why this ticket exists

This is the epic's `TelegramService.send`. Every app-initiated message from every feature enters here, so quiet hours, pause and caps are impossible to skip. It does not deliver; delivery is the worker's job (BE-031).

## Read first

- `api/app/telegram/service.py` (`reply`, BE-021).
- `api/app/notifications/policy.py`: `decide`, `local_day_start`.
- `api/app/telegram/repository.py`: `enqueue`, `count_sent_since`.

## Design

- **Pattern:** Facade over policy + outbox; the message is a command value stored for later execution.
- **Data flow:** feature → `send(...)` → check template → `get_policy` → `count_sent_since` → `decide` → `enqueue(status, scheduled_for)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/service.py` (changed).
- `api/tests/test_telegram_service_send.py` (new).

**Function**

```python
async def send(
    session: AsyncSession, *,
    chat_id: int,
    template: str,
    data: Mapping[str, str],
    category: str,
    idempotency_key: str,
    now: datetime,
    buttons: tuple[tuple[ButtonSpec, ...], ...] = (),
) -> TelegramOutbound
```

1. `templates.render(template, data)` as a dry run: an unknown template or missing field fails here, at the call site, not hours later in the worker.
2. `policy = await get_policy(session)`; `sent = await count_sent_since(session, category, local_day_start(now, policy))`.
3. `decision = decide(category, policy, now, sent)`.
4. `SendNow` → `status="queued", scheduled_for=now`. `Defer(until)` → `status="deferred", scheduled_for=until`.
5. `enqueue(...)` and return the row. A repeated `idempotency_key` returns the original row untouched.

Rules: `category` matches `^[a-z][a-z0-9_-]{0,29}$`; `idempotency_key` is 1–120 characters; `now` is timezone-aware. Violations raise `ValueError`.

Convention for callers, documented in the docstring: `idempotency_key = "<feature>:<what>:<id>:<period>"`, e.g. `radar:digest:2026-11-15`.

## Steps

1. Write `send` step by step.
2. Tests for each decision path using a real database and a fixed `now`.

## Tests

- `test_daytime_message_is_queued_for_now`
- `test_quiet_hours_message_is_deferred_to_morning`
- `test_paused_message_is_deferred_to_pause_end`
- `test_capped_category_is_deferred_to_next_day`
- `test_same_idempotency_key_returns_same_row`
- `test_unknown_template_raises_and_stores_nothing`
- `test_missing_template_field_raises_and_stores_nothing`
- `test_bad_category_or_naive_now_raises`

## Acceptance criteria

- [ ] No path stores a message without consulting the policy
- [ ] A bad template fails before anything is stored
- [ ] Calling twice with one key stores one row
- [ ] `send` performs no Telegram call
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The five steps in order.
2. Nothing in `send` imports the sender.
3. The docstring's key convention: is it one you would follow?

Things that should *not* be in the diff: delivery, retries, grouping of rows.

## Out of scope

- Delivering queued rows → BE-031.
- Edit and delete → BE-033.

## Notes / log

The agent adds progress notes, decisions and open questions here.
