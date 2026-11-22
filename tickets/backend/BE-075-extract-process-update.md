# BE-075: Extract `process_update` from the webhook (no behaviour change)

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-011: Telegram debugger: explain and replay](../../Epics/EPIC-011-telegram-debugger-explain-replay.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** BE-015
- **Can run in parallel with:** BE-072, BE-073, BE-077
- **Public endpoint?** no
- **Review size:** ~60 lines moved, 2 files, ~10 min

## Goal

Everything the webhook does after parsing an update lives in one function, `process_update`, and the webhook route just calls it.

## Why this ticket exists

'Run for real' (BE-076) must use the very same path as a real update: allowlist, claim, route, handler, mark. Extracting that path first, as a pure move, means the playground cannot grow a second, slightly different pipeline. Refactor before feature.

## Read first

- `api/app/telegram/webhook.py` as it is on `main` when you start: the order secret → parse → allowlist → claim → route → handler → mark.
- `api/tests/test_telegram_webhook.py`: the tests that must stay green untouched.

## Design

- **Pattern:** Refactor before feature: a behaviour-preserving extraction, verified by unchanged tests.
- **Data flow:** webhook route → parse → `process_update(update, deps)` → `ProcessOutcome` → ack.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/pipeline.py` (new):

```python
class ProcessOutcome(BaseModel):     # frozen
    status: Literal["ignored", "duplicate", "processed", "failed"]
    route: str = ""                  # the route target, when one was chosen

async def process_update(update: InboundUpdate, *, session: AsyncSession, settings: Settings, now: datetime, ...) -> ProcessOutcome
```
  The parameter list is whatever the webhook body needs at the time (for example the sender, once BE-021 is merged). Move the code; do not redesign it.
- `api/app/telegram/webhook.py` (changed): the route keeps the secret guard and parsing, calls `process_update`, returns the ack whatever the outcome.

**Rules**

- No behaviour change. Existing webhook tests pass **without edits**.
- Log lines keep their names and still carry no update content.

## Steps

1. Run the webhook tests and note they pass.
2. Move the body into `process_update`.
3. Add direct tests for the new function.
4. Run `make api-test`.

## Tests

- `test_process_update_ignores_strangers`.
- `test_process_update_reports_duplicate`.
- `test_process_update_runs_handler_and_marks_processed`.
- `test_process_update_marks_failed_when_handler_raises`.
- All existing `test_telegram_webhook.py` tests pass unchanged.

## Acceptance criteria

- [ ] `process_update` holds the allowlist, claim, route, handler and mark steps in the original order
- [ ] The webhook route only guards, parses, calls it and acks
- [ ] No existing test was edited
- [ ] The four outcomes are each covered by a direct test
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `git diff --stat`: `webhook.py` shrinks, `pipeline.py` appears.
2. `make api-test`: green, with `git diff api/tests/test_telegram_webhook.py` empty.

## Review guide

Read the diff in this order, and check:

1. Read `pipeline.py` next to the old `webhook.py`: is it a move, line for line?
2. Did any test expectation change? It should not.

Things that should *not* be in the diff: New behaviour, new log lines, playground code.

## Out of scope

- Calling it from the playground → BE-076.

## Notes / log

The agent adds progress notes, decisions and open questions here.
