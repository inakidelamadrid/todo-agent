# BE-074: `POST /admin/telegram/explain`: dry-run route explanation

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-068, BE-069, BE-072, BE-073
- **Can run in parallel with:** BE-075, BE-077
- **Public endpoint?** no
- **Review size:** ~50 lines, 1 file plus tests, ~10 min

## Goal

An admin posts a composed update (or a sample name) and gets the step-by-step explanation back. Nothing is stored and no handler runs.

## Why this ticket exists

Joins the two pure pieces (compose, explain) behind the guarded router. Dry run only: the real run is a separate, confirmed endpoint (BE-076) so the safe path and the side-effect path can never be confused.

## Read first

- `api/app/telegram/playground/router.py`, `compose.py`, `explain.py`.
- `api/app/settings.py`: `telegram_allowed_user_id`.

## Design

- **Pattern:** Plain route: validate → pure functions → response. One write: the action record.
- **Data flow:** body → `ComposedUpdate` → `compose_update(user_id=allowed_user_id, update_id=0)` → `explain_route(already_seen=False)` → response; `record_action(…, "explain", …)`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/telegram/playground/router.py` (changed).

**Request** (one of the two forms):

```json
{"update": {"kind": "command", "text": "/help"}}
{"sample": "help-command"}
```

**Responses**

- `200`: the `RouteExplanation` in camelCase, e.g. `{"steps": [{"name": "allowlist", "verdict": "pass", "detail": "…"}, …], "finalRoute": {"kind": "command", "target": "core.help", "arg": ""}}`.
- `422`: invalid update, both or neither form given, unknown sample.
- `409`: `TELEGRAM_ALLOWED_USER_ID` is not set (there is no chat to act as). Detail names the variable.

Also `GET /admin/telegram/samples` → `{"samples": ["help-command", …]}` so the UI can list them.

The composed text is used in memory only: not stored, not logged, not echoed back. `telegram_updates` is not touched.

## Steps

1. Request model.
2. Routes.
3. Tests.
4. Run `make api-test`.

## Tests

- `test_explain_without_credentials_returns_401`: no credentials → `401`.
- `test_explain_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_explain_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_explain_when_playground_off_returns_404`: playground switched off → `404`.
- `test_explain_command_returns_steps_and_route`.
- `test_explain_by_sample_name`.
- `test_unknown_sample_or_both_forms_is_422`.
- `test_explain_without_allowed_user_id_is_409`.
- `test_explain_writes_nothing_to_telegram_updates`.
- `test_explain_response_does_not_echo_text`.
- `test_explain_records_an_action`.

## Acceptance criteria

- [ ] An admin gets the explanation for a composed update or a sample
- [ ] The four guard cases hold
- [ ] `telegram_updates` is unchanged after a call
- [ ] The submitted text is not in the response or any log line
- [ ] The call is recorded as an `explain` action
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. Playground on, as admin from the console: POST `{sample: 'help-command'}` to `/api/admin/telegram/explain` → three steps and `core.help`.

## Review guide

Read the diff in this order, and check:

1. The route: does anything write besides `record_action`?
2. Is the acting user always `telegram_allowed_user_id`?

Things that should *not* be in the diff: Running handlers, sending messages.

## Out of scope

- Run for real → BE-076.
- The panel → FE-025, FE-026.

## Assumptions

- With several admins later, every admin acts as the one allowlisted Telegram account (`TELEGRAM_ALLOWED_USER_ID`); per-admin chats are not planned.

## Notes / log

The agent adds progress notes, decisions and open questions here.
