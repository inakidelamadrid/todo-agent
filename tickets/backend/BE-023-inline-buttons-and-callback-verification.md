# BE-023: Inline buttons and verified button taps

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Router step 1, §5.3, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-021, BE-022
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~90 lines, 4 files, ~12 min

## Goal

Replies can carry signed buttons, and a tap reaches its handler only when its signature is valid and unexpired.

## Why this ticket exists

BE-022 made the signing functions; this ticket uses them on both sides of the round trip: when building a button and when a tap arrives.

## Read first

- `api/app/telegram/callbacks.py`, `routing.py`, `webhook.py`.
- Telegram shows a loading spinner on a tapped button until the bot calls `answerCallbackQuery`, so every tap must be answered, valid or not.

## Design

- **Pattern:** Token guard at the edge: verification happens in the webhook, before routing; handlers only ever see verified actions.
- **Data flow:** tap → `verify_callback` → invalid: `answer_callback(expired)`; valid: `Route("callback", action, arg)` → handler → `answer_callback("")`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/callbacks.py` (changed): `make_button`.
- `api/app/telegram/handlers.py` (changed): `Reply.buttons`.
- `api/app/telegram/service.py`, `webhook.py` (changed).
- `api/tests/test_telegram_buttons.py` (new).

**Building**

```python
def make_button(text: str, action: str, arg: str, *, secret: str, today: date,
                lifetime_days: int = DEFAULT_BUTTON_LIFETIME_DAYS) -> Button
```
Pure. `Reply` gains `buttons: tuple[tuple[ButtonSpec, ...], ...] = ()`, where `ButtonSpec` is a frozen `(text, action, arg)`; handlers never see the secret. `service.reply` turns specs into signed `Button`s.

**Verifying** (webhook, for `CALLBACK` updates, before routing):

- `verify_callback(update.callback_data, secret, today)` returns `None` → `answer_callback(update.callback_id, render("expired_button"))`, `mark_update(..., "processed", "callback.rejected")`, return the ack. No handler runs.
- Valid → `Route(kind="callback", target=action.action, arg=action.arg)`, dispatched like any other route, then `answer_callback(update.callback_id, "")`.
- `routing.route` no longer returns `callback.unverified`; callback routes are built only here. Remove that branch and its test.

## Steps

1. Add `make_button` and `ButtonSpec`.
2. Sign buttons in `service.reply`.
3. Verify taps in the webhook.
4. Tests with a test-only handler registered under `test.echo`.

## Tests

- `test_reply_buttons_are_signed_and_verifiable`
- `test_valid_tap_runs_handler_with_arg`
- `test_tampered_tap_is_answered_as_expired_and_runs_nothing`
- `test_expired_tap_is_rejected`
- `test_every_tap_is_answered_once`
- `test_tap_from_stranger_is_dropped_before_verification`

## Acceptance criteria

- [ ] A handler can only be reached by a tap whose data verifies
- [ ] Rejected taps get the calm `expired_button` notice and run no handler
- [ ] Every tap from the owner results in exactly one `answer_callback`
- [ ] Handlers never receive the signing secret
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

By hand, once a feature sends a button: tap it (works), then wait past expiry or edit the data in a recorded payload and replay it with curl (rejected).

## Review guide

Read the diff in this order, and check:

1. `webhook.py`: verification sits before `resolve`; the rejected branch returns early.
2. `service.reply`: the only place a secret meets a button.
3. `routing.py`: the unverified branch is gone.

Things that should *not* be in the diff: feature buttons (each epic adds its own).

## Out of scope

- Buttons on queued messages → BE-030.
- The keep/discard buttons → BE-045.

## Notes / log

The agent adds progress notes, decisions and open questions here.
