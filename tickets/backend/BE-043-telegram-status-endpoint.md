# BE-043: GET /integrations/telegram/status

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-011, BE-019, BE-029
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 4 files, ~12 min

## Goal

A protected endpoint reports whether Telegram is configured and healthy: webhook state, outbox counts and recent update counts.

## Why this ticket exists

It feeds the status card in the web app (FE-006, FE-007) and gives one place to look before reaching for the terminal.

## Read first

- `api/app/bills/router.py`.
- `api/scripts/telegram_webhook.py` (BE-039): `get_webhook_info` is already used there.

## Design

- **Pattern:** Thin controller over small repository counts and one port call.
- **Data flow:** request → `sender.webhook_info()` + `outbound_counts(session)` + `update_counts(session, since)` → `TelegramStatus`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/status.py` (new): schema and route, on its **own router protected by `require_api_key`** (not the webhook router).
- `api/app/telegram/sender.py`, `aiogram_sender.py` (changed): `webhook_info: Callable[[], Awaitable[WebhookInfo]]`, where `WebhookInfo` is our frozen type (`url_host`, `pending_update_count`, `last_error_at`, `last_error_message`).
- `api/app/telegram/repository.py` (changed): `outbound_counts(session)`, `update_counts(session, since)`.
- `api/tests/test_telegram_status_api.py` (new).

**Response** (`200`)

```json
{
  "configured": true,
  "reachable": true,
  "webhook": {"urlHost": "abc.ngrok.app", "pendingUpdateCount": 0, "lastErrorAt": null, "lastErrorMessage": null},
  "outbound": {"queued": 0, "deferred": 2, "failed": 0, "lastSentAt": "2026-11-15T15:04:05Z"},
  "updates": {"last24h": 12, "failed24h": 0}
}
```

- Token unset → `configured: false`, `reachable: false`, `webhook: null`; counts still returned.
- Telegram call fails → `reachable: false`, `webhook: null`; still `200`.
- Only the URL **host** is returned, never the path or anything secret.

## Steps

1. `webhook_info` on the port, adapter and fake.
2. The two count functions.
3. Schema and route; mount with the API key dependency.
4. Tests.

## Tests

- `test_status_requires_api_key`, `test_status_rejects_wrong_key`
- `test_status_is_not_reachable_with_the_telegram_secret_alone`
- `test_unconfigured_status`
- `test_unreachable_telegram_still_returns_200`
- `test_counts_reflect_rows`
- `test_response_is_camel_case_and_has_host_only`

## Acceptance criteria

- [ ] The route requires a valid API key
- [ ] It never returns a token, a secret or a full webhook URL
- [ ] It answers `200` whether or not Telegram is reachable
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

From `http://127.0.0.1:8000/docs`, authorise with your key and call the endpoint; compare with `make telegram-info`.

## Review guide

Read the diff in this order, and check:

1. `main.py`: this router has `require_api_key`; the webhook router still does not.
2. The response model: nothing sensitive.
3. The two failure modes.

Things that should *not* be in the diff: frontend; alerting.

## Out of scope

- The status card → FE-006, FE-007.

## Notes / log

The agent adds progress notes, decisions and open questions here.
