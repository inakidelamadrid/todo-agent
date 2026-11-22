# BE-004: Telegram settings (bot token, webhook secret, allowed user ID)

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.1, §7
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-005, BE-010, BE-018, BE-020, BE-024, BE-026, BE-029, BE-036
- **Public endpoint?** no
- **Review size:** ~40 lines, 3 files, ~5 min

## Goal

The API can read its Telegram configuration from the environment as immutable, validated settings, and the app still starts when none of it is set.

## Why this ticket exists

Every later Telegram ticket needs the token, the webhook secret or the allowed user ID. Adding them alone, first, means the reviewer sees the secrets handling once, in isolation, before any code uses it.

## Read first

- `api/app/settings.py`: the frozen `Settings` model and how `SecretStr` is used for the Postgres password.
- `api/.env.example`: the format for documenting a variable.
- `SecretStr`: a Pydantic type whose `repr` is `**********`, so the value cannot leak through logs or tracebacks. You read it with `.get_secret_value()`.

## Design

- **Pattern:** Immutable settings, fail closed. Unset values are allowed (the app must start without Telegram), but anything that depends on them must treat "unset" as "deny".
- **Data flow:** environment → `Settings` (frozen) → `telegram_enabled(settings)` → later dependencies.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/settings.py` (changed): three new fields on `Settings`.
  - `telegram_bot_token: SecretStr = SecretStr("")`
  - `telegram_webhook_secret: SecretStr = SecretStr("")`
  - `telegram_allowed_user_id: int | None = None`
- Same file: a validator on `telegram_webhook_secret`. Empty is allowed. A non-empty value must match `^[A-Za-z0-9_-]{16,256}$` (Telegram allows 1–256 of these characters; we require at least 16). Otherwise raise `ValueError("TELEGRAM_WEBHOOK_SECRET must be 16-256 characters of A-Z a-z 0-9 _ -")`. The message must not contain the value.
- Same file: a pure function `telegram_enabled(settings: Settings) -> bool`, true only when all three values are set.
- `api/.env.example` (changed): add `TELEGRAM_BOT_TOKEN=`, `TELEGRAM_WEBHOOK_SECRET=`, `TELEGRAM_ALLOWED_USER_ID=` with one comment line each, including how to generate a secret: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.
- `api/tests/test_settings_telegram.py` (new).

## Steps

1. Add the three fields and the validator.
2. Add `telegram_enabled`.
3. Document the variables in `api/.env.example`.
4. Write the tests.

## Tests

- `test_app_starts_without_telegram_settings`: `Settings()` with only `API_KEYS` builds; `telegram_enabled` is false.
- `test_telegram_enabled_needs_all_three`: any one missing → false; all set → true.
- `test_short_webhook_secret_is_rejected`: 15 characters → `ValidationError`.
- `test_webhook_secret_with_bad_characters_is_rejected`: a value containing `!` → `ValidationError`.
- `test_secrets_do_not_appear_in_repr`: `repr(settings)` contains neither the token nor the secret.

## Acceptance criteria

- [ ] `Settings` has the three fields with the types and defaults above
- [ ] A malformed webhook secret fails at startup with a message that does not echo the value
- [ ] `repr(settings)` never shows the token or the secret
- [ ] `api/.env.example` documents the three variables with empty placeholders
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

Then start `make api-dev` with no Telegram variables set: it must start normally.

## Review guide

Read the diff in this order, and check:

1. `api/app/settings.py`: are both secrets `SecretStr`? Does the validator's error message avoid the value?
2. `api/.env.example`: placeholders only, no real values.
3. Tests: is the "app starts without Telegram" case covered?

Things that should *not* be in the diff: any route, any aiogram import, any real token.

## Out of scope

- Reading the settings in a route → BE-007.
- The callback-signing secret → BE-022.
- Getting the real values from BotFather → BE-040.

## Assumptions

- The allowed user ID comes from the environment for now. You chose one-time `/start` pairing but deferred it (question 3); BE-046 replaces this variable when that is designed.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-004-telegram-settings`. Three files touched, as the ticket scoped: `settings.py`, `.env.example`, `test_settings_telegram.py`.
- Fields + validator exactly per ticket; `telegram_enabled` returns true only when all three are present (empty `SecretStr`, `None` user ID, or empty secret → false).
- **Decision beyond the ticket:** one test caught that pydantic echoes the offending input in `str(ValidationError)` even when the validator's own message doesn't. Fix: `hide_input_in_errors=True` in `Settings.model_config`, applied model-wide (also protects `API_KEYS` and future secrets from echoing typos at startup).
- `make api-test` → 84 passed. App still starts with no Telegram variables set (covered by `test_app_starts_without_telegram_settings`).
