# BE-022: Signed callback data (HMAC) for inline buttons

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3, §7, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-004
- **Can run in parallel with:** BE-005 to BE-021
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~15 min

## Goal

Two pure functions create and verify button payloads that cannot be forged, altered or used after they expire, within Telegram's 64-byte limit.

## Why this ticket exists

A button's payload comes back to us from the client. Without a signature, anyone who learns the format could craft `expense:delete:<id>`. Signing is a self-contained piece of cryptography, so it is reviewed alone, with no Telegram code around it.

## Read first

- `hmac` and `hashlib` in the standard library.
- HMAC in two sentences: a keyed hash. Only someone holding the secret can produce the signature for a message, and changing one character of the message changes the signature completely.
- `api/app/security.py`: constant-time comparison.

## Design

- **Pattern:** Pure sign/verify pair returning a value or `None` (Result over exceptions): an invalid button is an expected outcome, not an error.
- **Data flow:** `(action, arg, expires_on)` → `sign_callback` → `"action:arg:exp:sig"` → Telegram → `verify_callback` → `CallbackAction | None`.

## Packages

None new. Standard library and what is already installed.

Hand-written instead of a package: about 40 lines over `hmac`. `itsdangerous` was considered: its signed tokens are too long for 64 bytes.

## Details

**Files**

- `api/app/settings.py` (changed): `telegram_callback_secret: SecretStr = SecretStr("")`; same character rule as the webhook secret, minimum 32. Add to `api/.env.example`.
- `api/app/telegram/callbacks.py` (new).
- `api/tests/test_telegram_callbacks.py` (new).

**Format** (ASCII, `:`-separated, at most 64 bytes):

| Part | Rule | Max length |
|---|---|---|
| `action` | `^[a-z][a-z0-9._-]*$`, e.g. `expense.recategorise` | 24 |
| `arg` | `^[A-Za-z0-9_-]*$`; a UUID is passed as 22-character base64url | 22 |
| `exp` | expiry day as days since 1970-01-01, base 36 | 4 |
| `sig` | first 10 characters of base64url(HMAC-SHA256(secret, `action:arg:exp`)): 60 bits | 10 |

**Functions (pure)**

```python
class CallbackAction(BaseModel):    # frozen
    action: str
    arg: str

DEFAULT_BUTTON_LIFETIME_DAYS = 7

def sign_callback(action: str, arg: str, expires_on: date, secret: str) -> str
def verify_callback(data: str, secret: str, today: date) -> CallbackAction | None
def uuid_to_arg(value: UUID) -> str
def arg_to_uuid(arg: str) -> UUID | None
```

- `sign_callback` raises `ValueError` when a part breaks its rule, the result exceeds 64 bytes, or the secret is empty.
- `verify_callback` returns `None` when: the shape is wrong; the signature differs (`hmac.compare_digest`); `today > expires_on`; or the secret is empty.

**Replay.** A valid button can be tapped twice until it expires. The signature does not prevent that; handlers behind buttons must therefore be idempotent, and say so in their own tickets.

## Steps

1. Add the setting.
2. Write `sign_callback` and `verify_callback` with round-trip tests.
3. Add the UUID helpers.
4. Add the tamper and expiry tests.

## Tests

- `test_round_trip`
- `test_signed_data_is_at_most_64_bytes_for_longest_inputs`
- `test_tampered_action_is_rejected`
- `test_tampered_arg_is_rejected`
- `test_tampered_expiry_is_rejected`
- `test_expired_is_rejected_and_last_day_is_accepted`
- `test_wrong_secret_is_rejected`
- `test_empty_secret_never_verifies`
- `test_garbage_input_returns_none`: `""`, `"a:b"`, 200 characters.
- `test_uuid_round_trip_is_22_chars`

## Acceptance criteria

- [ ] Verification uses `hmac.compare_digest`
- [ ] Altering any single character of signed data makes verification return `None`
- [ ] Signed data never exceeds 64 bytes
- [ ] Both functions are pure: the secret and the date are arguments
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `sign_callback`: exactly what bytes are signed? It must include action, arg and expiry.
2. `verify_callback`: every `return None` path; the comparison is constant-time.
3. The length table against the 64-byte limit.

Things that should *not* be in the diff: aiogram, routes, button building.

## Out of scope

- Building buttons and verifying taps in the webhook → BE-023.

## Assumptions

- Buttons expire after 7 days (the epic says "N days").
- The signature is truncated to 60 bits to fit 64 bytes. Guessing it needs about 10^18 attempts against a rate-limited webhook (BE-044); say so if you want a longer signature and shorter action names.

## Notes / log

The agent adds progress notes, decisions and open questions here.
