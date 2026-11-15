# BE-007: Webhook guard: require_telegram_secret dependency

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2, §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-004
- **Can run in parallel with:** BE-005, BE-006
- **Public endpoint?** no
- **Review size:** ~40 lines, 2 files, ~8 min

## Goal

A shared FastAPI dependency rejects any request that does not carry the configured `X-Telegram-Bot-Api-Secret-Token` header.

## Why this ticket exists

The webhook is the first endpoint that is not protected by `X-API-Key`: Telegram cannot send our key, so it sends a secret we registered with it instead. The guard ships before the route, so the route never exists unguarded, and so this one security idea is reviewed alone.

## Read first

- `api/app/security.py`: `require_api_key`. The new dependency is its twin.
- https://core.telegram.org/bots/api#setwebhook, the `secret_token` parameter.
- Constant-time comparison: `secrets.compare_digest` takes the same time whether the first or the last character differs, so an attacker cannot guess a secret one character at a time by measuring response times.

## Design

- **Pattern:** Token guard as a shared dependency (never an inline check in the route), failing closed.
- **Data flow:** request header → `require_telegram_secret` → `401`, or the route runs.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/security.py` (new).
- `api/tests/test_telegram_security.py` (new).

**Function**

```python
TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"

def require_telegram_secret(
    settings: Annotated[Settings, Depends(get_settings)],
    provided: Annotated[str | None, Header(alias=TELEGRAM_SECRET_HEADER)] = None,
) -> None
```

- Raises `HTTPException(401, detail="Invalid or missing Telegram secret")` when:
  - the header is missing;
  - the header does not match (compare with `secrets.compare_digest`);
  - **the configured secret is empty.** An unconfigured server must reject everything, never accept everything.
- Never logs or echoes the provided or the expected value.

**Tests** mount a throwaway probe route with this dependency, the way `api/tests/conftest.py` does for `require_api_key`.

## Steps

1. Write the dependency.
2. Add a probe-router fixture.
3. Write the four tests.

## Tests

- `test_missing_header_is_401`
- `test_wrong_secret_is_401`
- `test_correct_secret_passes`
- `test_unconfigured_secret_rejects_everything`: with `TELEGRAM_WEBHOOK_SECRET` unset, even an empty header value → `401`.
- `test_error_body_does_not_contain_the_secret`

## Acceptance criteria

- [ ] Missing, wrong or unconfigured secret → `401`
- [ ] The comparison uses `secrets.compare_digest`
- [ ] Neither value appears in any response or log
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `security.py`: find the empty-secret branch. Is it impossible to reach the route with an empty configured secret?
2. Is the comparison constant-time?
3. Tests: all four outcomes.

Things that should *not* be in the diff: the webhook route itself; changes to `require_api_key`.

## Out of scope

- The route that uses it → BE-008.
- Rate limiting → BE-044.

## Notes / log

The agent adds progress notes, decisions and open questions here.
