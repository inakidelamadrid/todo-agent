# FE-007: Wire the Telegram status card into the settings sheet

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** FE-005, FE-006, BE-043
- **Can run in parallel with:** none
- **Review size:** ~80 lines, 4 files, ~10 min

## Goal

The notification settings sheet shows live Telegram status, loaded from `GET /integrations/telegram/status`.

## Why this ticket exists

Last frontend step: the card from FE-006 gets real data. Small on purpose, since the client, store and component patterns are all established by now.

## Read first

- `web/src/features/notifications/api/client.ts` and `store/useNotificationsStore.ts` (FE-003, FE-005).
- `web/src/features/telegram/components/TelegramStatusCard.tsx`.

## Design

- **Pattern:** Typed client function + a small store slice + a narrow selector.
- **Data flow:** sheet opens → `loadStatus()` → `telegramApi.status()` → store → `TelegramStatusCard`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/telegram/api/client.ts` (new) and test: `createTelegramApi(fetchImpl?, base?)` → `{ status(): Promise<TelegramStatus> }`.
- `web/src/features/telegram/store/useTelegramStore.ts` (new) and test: `{ status, load: 'idle'|'loading'|'ready'|'error', loadStatus() }`.
- `web/src/features/notifications/components/NotificationSettingsSheet.tsx` (changed): render the card above the form; call `loadStatus()` when the sheet opens.

**Behaviour**

- Status loads each time the sheet opens (it is live information; no caching beyond the open sheet).
- A status failure shows the card's error state only. The settings form below still works: the two loads are independent.
- No polling.

## Steps

1. Client function and test.
2. Store slice and test.
3. Place the card in the sheet.
4. Browser check.

## Tests

- `status calls GET /integrations/telegram/status`
- `loadStatus moves idle → loading → ready`
- `loadStatus failure sets error and keeps the previous status`

## Acceptance criteria

- [ ] The sheet shows the real status from the API
- [ ] A status failure does not block the settings form
- [ ] No polling or timers are introduced
- [ ] Checked in the browser at desktop and mobile widths
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With the API running and the dev bot configured: open Notifications: the card says Connected with your ngrok host. Stop ngrok and send the bot a message, reopen: the webhook error appears after Telegram's next attempt.

## Review guide

Read the diff in this order, and check:

1. The two loads are independent in the sheet.
2. The client function: one line over `createRequest`.

Things that should *not* be in the diff: a rail chip for Telegram; auto-refresh.

## Out of scope

- A rail indicator → only if you find you want one after using it.

## Notes / log

The agent adds progress notes, decisions and open questions here.
