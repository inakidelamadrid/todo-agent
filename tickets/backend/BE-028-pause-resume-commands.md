# BE-028: /pause and /resume commands

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-021, BE-026
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~60 lines, 3 files, ~10 min

## Goal

`/pause` stops app-initiated notifications until tomorrow morning (or for a given duration) and `/resume` lifts it; both confirm in the chat.

## Why this ticket exists

It is the first real feature handler registered in the registry from BE-015, so it also proves that adding a command needs no webhook change.

## Read first

- `api/app/telegram/handlers.py`: the `Handler` signature and `HANDLERS`.
- `api/app/notifications/policy.py`: `quiet_end_after`.

## Design

- **Pattern:** Thin handler over a pure parser: the handler loads and saves; a pure function works out the date.
- **Data flow:** `/pause 2h` → `parse_pause(args, now, policy)` → `save_policy(paused_until=…)` → `Reply("paused")`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/notifications/telegram_handlers.py` (new).
- `api/app/telegram/handlers.py` (changed): two registry entries. `api/app/telegram/templates.py` (changed): three templates.
- `api/tests/test_pause_resume.py` (new).

**Pure function**

```python
def parse_pause(args: str, now: datetime, policy: NotificationPolicy) -> datetime | None
```

| `args` | Result |
|---|---|
| `""` | the next end of quiet hours after tonight (i.e. tomorrow 08:00 local) |
| `30m`, `2h`, `3d` | `now` + that duration; limits: 1 minute to 30 days |
| anything else | `None` |

**Handlers**

- `notifications.pause`: `None` → `Reply("pause_usage")`. Otherwise save `paused_until` and reply `paused` with `{until}` formatted in the policy's zone, e.g. `tomorrow 08:00` / `Thu 14:30`.
- `notifications.resume`: set `paused_until = None`, reply `resumed`. Resuming when not paused replies the same (idempotent).

**Templates**: `paused` = `Paused until {until}. /resume to undo.`; `resumed` = `Notifications are back on.`; `pause_usage` = `Use /pause, /pause 2h or /pause 3d.`

## Steps

1. `parse_pause` with its table as tests.
2. The two handlers.
3. Register them and add the templates.
4. Webhook-level test.

## Tests

- `test_parse_pause_default_is_next_morning`
- `test_parse_pause_minutes_hours_days`
- `test_parse_pause_rejects_garbage_and_out_of_range`
- `test_pause_command_saves_policy_and_replies`
- `test_resume_clears_pause`
- `test_resume_when_not_paused_is_fine`
- `test_pause_bad_argument_replies_usage_and_saves_nothing`

## Acceptance criteria

- [ ] `/pause`, `/pause 2h` and `/resume` behave as in the tables
- [ ] `webhook.py` is unchanged by this ticket
- [ ] `parse_pause` is pure
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With the dev bot: send `/pause 1h`, then `GET /settings/notifications` shows `pausedUntil` about an hour ahead; send `/resume`, it is `null`.

## Review guide

Read the diff in this order, and check:

1. `parse_pause`: limits and the default.
2. The handlers: load, decide, save, reply.
3. The diff does not touch `webhook.py`.

Things that should *not* be in the diff: deferring queued messages (the policy check in BE-030 does that).

## Out of scope

- Pause on the settings screen → FE-004.

## Notes / log

The agent adds progress notes, decisions and open questions here.
