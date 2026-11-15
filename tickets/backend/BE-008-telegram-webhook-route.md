# BE-008: Webhook route that accepts and parses updates

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2
- **Assigned agent / harness / model:**
- **Depends on:** BE-006, BE-007
- **Can run in parallel with:** none
- **Public endpoint?** **yes**: `POST /integrations/telegram/webhook` has no API key. It is guarded by `require_telegram_secret` (BE-007). The epic makes this endpoint public explicitly (§5.2).
- **Review size:** ~60 lines, 3 files, ~10 min

## Goal

`POST /integrations/telegram/webhook` exists, is guarded by the Telegram secret, parses the body into an `InboundUpdate`, and answers `200` without doing anything else yet.

## Why this ticket exists

This is the skeleton every inbound ticket hangs on. Keeping it empty of behaviour lets the reviewer check only the wiring: where it is mounted, what guards it, and what it returns to Telegram.

## Read first

- `api/app/main.py`: how routers are mounted, and the "protected by default" comment.
- `api/app/bills/router.py`: a thin route.
- Telegram retries a webhook delivery whenever the response is not 2xx. So the route answers `200` even for payloads it cannot use; a non-2xx is only for requests that are not from Telegram.

## Design

- **Pattern:** Thin controller: guard → parse → (nothing yet) → respond.
- **Data flow:** Telegram → `require_telegram_secret` → `Update.model_validate` → `to_inbound` → `200 {"ok": true}`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/webhook.py` (new).
- `api/app/main.py` (changed): mount the router.
- `api/tests/test_telegram_webhook.py` (new).

**Route**

```python
telegram_webhook_router = APIRouter(
    prefix="/integrations/telegram",
    tags=["telegram"],
    dependencies=[Depends(require_telegram_secret)],
)

@telegram_webhook_router.post("/webhook", include_in_schema=False)
async def receive_update(payload: dict[str, Any]) -> WebhookAck
```

- `WebhookAck`: frozen model, `{"ok": true}`.
- Body parses → build the `InboundUpdate` and discard it (later tickets use it).
- Body is JSON but not a valid `Update` → still `200 {"ok": true}`, and log one warning line `telegram.unparseable` with no payload content.
- Body is not JSON → FastAPI's `422` is acceptable; Telegram never sends this.

**Mounting.** In `create_app`, include the router **without** `require_api_key`, directly under the public router, with a comment: `# Public by ticket BE-008: guarded by the Telegram secret token, not an API key.`

## Steps

1. Write the router and the ack model.
2. Mount it in `create_app` with the comment.
3. Write the tests using the BE-005 fixtures.

## Tests

- `test_webhook_without_secret_is_401`
- `test_webhook_with_wrong_secret_is_401`
- `test_webhook_with_api_key_but_no_secret_is_401`: a valid `X-API-Key` alone does not open it.
- `test_webhook_accepts_each_fixture` (parametrised): `200` and `{"ok": true}`.
- `test_unparseable_update_is_still_200`: body `{"foo": 1}`.
- `test_webhook_is_not_in_openapi`

## Acceptance criteria

- [ ] The route answers `200 {"ok": true}` to every fixture when the secret matches
- [ ] Without the correct secret it answers `401`, including when a valid API key is sent
- [ ] The route is absent from `/openapi.json`
- [ ] `main.py` carries the comment explaining why this router has no API key
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With `TELEGRAM_WEBHOOK_SECRET` set in `api/.env` and `make api-dev` running:

```bash
curl -i -X POST http://127.0.0.1:8000/integrations/telegram/webhook -H 'Content-Type: application/json' -d @api/tests/fixtures/telegram/text.json
```

Expect `401`. Add the header `X-Telegram-Bot-Api-Secret-Token` with your secret yourself and expect `200`.

## Review guide

Read the diff in this order, and check:

1. `main.py`: the new router is the only one besides `public` without `require_api_key`, and the comment says why.
2. `webhook.py`: the guard is on the router, not inside the function.
3. The route does nothing with the update yet.

Things that should *not* be in the diff: allowlist checks, database access, replies.

## Out of scope

- Ignoring strangers → BE-009.
- De-duplication → BE-012.
- Routing → BE-013.

## Notes / log

The agent adds progress notes, decisions and open questions here.
