# EPIC-010: Telegram notification policy and outbox (infra)

- **Status:** in-tickets
- **Type:** infrastructure (part of foundation **F-6 Scheduler & notifications**)
- **Owner:** Ignacio
- **Split from:** [EPIC-008: Telegram integration](EPIC-008-telegram-integration.md) on 2026-11-22, so the bot can talk (replies and playground test messages) before any queue or policy exists.
- **Depends on:** EPIC-008 outbound basics (sender port, templates, `service.reply`: BE-018 to BE-021); F-6 queue and worker (BE-047 to BE-052)
- **Used by:** every feature that *initiates* a message (EPIC-001 payer alerts, EPIC-003 check-ins, EPIC-004 reminders and digest, EPIC-005 reset invite)

## 1. Summary

Messages the app starts on its own go through `service.send(...)`: the message is stored in an outbox, checked against one notification policy (quiet hours, pause, per-category caps, grouping), and delivered by a worker that honours Telegram's rate limits. Replies to something the owner just sent, and playground test messages, do **not** go through this: they use `service.reply` (EPIC-008) and go out immediately.

## 2. Goals

- One notification policy for every app-initiated message, enforced centrally.
- Nothing is dropped by the policy: deferred messages go out when the quiet window ends.
- Telegram's 429 limits are respected; repeated failure for important categories falls back to email.
- The owner can change quiet hours and pause from the web app and the bot.

## 3. Non-goals

- Policies for replies or playground test messages (those are immediate by design).
- A policy explainer tool in the playground (a later debugger tool).

## 4. Requirements

Moved from EPIC-008 §5.3:

- `service.send(chat, template, data, buttons?, category, idempotency_key)` stores an outbound row and returns its status (`queued` or `deferred` with `scheduledFor`).
- **Quiet hours** and **pause**: messages are deferred, not dropped, except categories marked urgent. Default quiet hours 20:00 to 08:00; no category breaks through by default (`urgentCategories` is configurable).
- **Per-category caps** (e.g. 1 grouped radar message per day).
- **Grouping window:** messages to the same chat within X minutes can merge.
- **Telegram rate limits:** a queue with throttling; on 429, honour `retry_after`.
- **Failure handling:** retries with backoff. If Telegram is unreachable for longer than N minutes, important categories fall back to email (EPIC-007).
- `/pause` and `/resume` commands; `GET`/`PATCH /settings/notifications`; a notification settings form in the web app.
- `GET /integrations/telegram/status` and its status card: webhook status, queue depth, last successful send, error rate (EPIC-008 §5.6), here because queue depth needs the outbox.

## 5. Data model

| Entity | Key fields |
|---|---|
| `TelegramOutbound` | id, chatId, template, category, status (`queued`/`sent`/`deferred`/`failed`), telegramMessageId?, idempotencyKey, attempts, scheduledFor? |
| `NotificationPolicy` | quietHours, pausedUntil?, perCategoryCaps, groupingWindowMinutes, urgentCategories |

## 6. Acceptance criteria

- [ ] Every app-initiated message goes through `service.send`. Quiet hours, pause, caps, grouping and 429 back-off are enforced centrally.
- [ ] A message sent during quiet hours is deferred and delivered when the window ends.
- [ ] `/pause` and `/resume` work, and the settings form changes the policy.
- [ ] Important categories fall back to email when Telegram stays unreachable.

## 7. Ticket breakdown

Moved from EPIC-008 unchanged (IDs kept). BE-031 to BE-032 need the F-6 tickets (BE-047 to BE-052).

**Start anywhere here:** BE-024, BE-029, FE-006.

Backend:

- [BE-024](../tickets/backend/BE-024-notification-policy-quiet-hours-pause.md): Notification policy: quiet hours and pause. Depends on: none
- [BE-025](../tickets/backend/BE-025-notification-policy-caps-grouping.md): Notification policy: per-category caps and grouping. Depends on: BE-024
- [BE-026](../tickets/backend/BE-026-notification-policy-storage.md): Store the notification policy (table and repository). Depends on: BE-025
- [BE-027](../tickets/backend/BE-027-notification-settings-endpoints.md): GET and PATCH /settings/notifications. Depends on: BE-026
- [BE-028](../tickets/backend/BE-028-pause-resume-commands.md): /pause and /resume commands. Depends on: BE-021, BE-026
- [BE-029](../tickets/backend/BE-029-telegram-outbound-table.md): Outbound message table and enqueue. Depends on: BE-010 (for the models module)
- [BE-030](../tickets/backend/BE-030-telegram-service-send.md): telegram service send(): the one function features call. Depends on: BE-020, BE-025, BE-026, BE-029
- [BE-031](../tickets/backend/BE-031-outbound-delivery-worker.md): Deliver due outbound messages. Depends on: BE-019, BE-030, BE-051, BE-052
- [BE-032](../tickets/backend/BE-032-rate-limit-and-backoff.md): Honour Telegram 429 retry_after and back off. Depends on: BE-031
- [BE-034](../tickets/backend/BE-034-email-fallback.md): Fall back to email when Telegram stays unreachable — **blocked**. Depends on: BE-031, BE-032, EPIC-007
- [BE-043](../tickets/backend/BE-043-telegram-status-endpoint.md): GET /integrations/telegram/status. Depends on: BE-011, BE-019, BE-029

Frontend:

- [FE-003](../tickets/frontend/FE-003-notification-settings-model-client.md): Notification settings: types, validation and API client. Depends on: FE-002, BE-027
- [FE-004](../tickets/frontend/FE-004-notification-settings-form.md): Notification settings form (presentational, all states). Depends on: FE-003
- [FE-005](../tickets/frontend/FE-005-wire-notification-settings.md): Wire notification settings: store, optimistic save, rail entry. Depends on: FE-004
- [FE-006](../tickets/frontend/FE-006-telegram-status-card.md): Telegram status card (presentational, all states). Depends on: none
- [FE-007](../tickets/frontend/FE-007-wire-telegram-status.md): Wire the Telegram status card into the settings sheet. Depends on: FE-005, FE-006, BE-043

Elsewhere but depending on these: BE-057 (F-6 job failure alert) needs BE-030 and BE-031; FE-008 needs FE-007.

## 8. Open questions (answered in EPIC-008, kept here)

1. Default quiet hours, and which categories may break through them?
   - Answer: Quiet hours 20:00 - 8:00
   - (assumed) No category breaks through quiet hours by default; `urgentCategories` is configurable (BE-024, BE-027).
2. Should important notifications fall back to email when Telegram fails?
   - Answer: Yes (deferred)
