# BE-076: `POST /admin/telegram/replay`: run a composed update for real

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-011: Telegram debugger: explain and replay](../../Epics/EPIC-011-telegram-debugger-explain-replay.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-074, BE-075
- **Can run in parallel with:** BE-077 to BE-079
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files plus tests, ~12 min

## Goal

An admin can send a composed update through the real pipeline, as the owner's own chat, after an explicit confirmation. The handler runs once and the run is marked as playground-made.

## Why this ticket exists

Epic question 11: the explainer may execute handlers, as an explicit, confirmed mode. It reuses `process_update`, so it is the real path, and it uses negative update IDs so it can never collide with, or be mistaken for, a real Telegram update.

## Read first

- `api/app/telegram/pipeline.py` (BE-075).
- `api/app/telegram/playground/router.py` and `compose.py`.
- Telegram `update_id` is always positive: https://core.telegram.org/bots/api#update

## Design

- **Pattern:** Reuse of the one pipeline; the only new logic is a pure ID generator.
- **Data flow:** body (`confirm: true`) → `compose_update(update_id=playground_update_id(now))` → `process_update` → outcome; `record_action(…, "replay", …)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/playground/compose.py` (changed): `def playground_update_id(now: datetime) -> int` (pure): the negative of `now` in microseconds since the epoch. Always `< 0`; fits a `BigInteger`.
- `api/app/telegram/playground/router.py` (changed).

**Request**

```json
{"update": {"kind": "command", "text": "/help"}, "confirm": true}
```
`confirm` must be the literal `true`; missing or false → `422`. A `sample` name is accepted in place of `update`, as in BE-074.

**Response `200`**

```json
{"updateId": -1794787245123456, "status": "processed", "route": "core.help"}
```
`status` is the `ProcessOutcome` status. `409` when `TELEGRAM_ALLOWED_USER_ID` is unset.

**Rules**

- The update always acts as the allowlisted account; nothing in the request can change the sender.
- The run goes through the allowlist, claim, router and handler like any update. Its row in `telegram_updates` has a negative `update_id`, which is how the update log marks it `playground: true` (BE-071).
- Whatever the handler does is real: a reply is sent to the owner's chat, records are created. That is the point, and why confirmation is required.
- Composed text is not logged and not echoed back.

## Steps

1. `playground_update_id` and its tests.
2. The route.
3. Tests with the recording sender fake.
4. Run `make api-test`.

## Tests

- `test_replay_without_credentials_returns_401`: no credentials → `401`.
- `test_replay_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_replay_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_replay_when_playground_off_returns_404`: playground switched off → `404`.
- `test_replay_without_confirm_is_422`.
- `test_replay_runs_the_handler_once_and_reports_route`.
- `test_replay_row_has_negative_update_id`.
- `test_replay_always_acts_as_allowed_user`.
- `test_playground_update_id_is_negative_and_increases_in_magnitude_with_time`.
- `test_replay_records_an_action_with_the_outcome`.

## Acceptance criteria

- [ ] A confirmed replay runs the real pipeline once and returns its outcome
- [ ] Without `confirm: true` nothing runs
- [ ] The stored update has a negative ID and shows as `playground: true` in the log
- [ ] The four guard cases hold
- [ ] The call is recorded as a `replay` action
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. Dev bot configured, playground on: POST `{sample: 'help-command', confirm: true}` → the help message arrives in your Telegram chat, and `GET /api/admin/telegram/updates` shows a row with `playground: true`.

## Review guide

Read the diff in this order, and check:

1. The route: is `process_update` the only thing that does work?
2. Can the request influence the sender or the update ID? It must not.
3. Is `confirm` enforced by the schema?

Things that should *not* be in the diff: A second pipeline, skipping the allowlist or the claim, bulk replays.

## Out of scope

- The confirmation dialog → FE-026.

## Notes / log

The agent adds progress notes, decisions and open questions here.
