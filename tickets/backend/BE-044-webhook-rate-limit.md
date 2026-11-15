# BE-044: Rate limit on the webhook

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-008
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~50 lines, 3 files, ~8 min

## Goal

The webhook answers `429` beyond a fixed number of requests per minute.

## Why this ticket exists

The webhook is the only route reachable without an API key. The secret check is cheap, but an attacker can still hammer it to guess the secret or the callback signature (60 bits, BE-022). A limit makes that impractical.

## Read first

- https://slowapi.readthedocs.io/
- `api/app/main.py`.

## Design

- **Pattern:** Guard as a decorator/dependency on the single public route.
- **Data flow:** request → limiter (per client IP) → `429`, or the secret guard and the route.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `slowapi` | **new** | Request rate limiting for Starlette/FastAPI | 0.1.10, MIT, released 2026-06-13. The usual FastAPI choice; built on the `limits` library (5.8.0, MIT). Hand-rolling counters was rejected: window arithmetic is easy to get subtly wrong. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add slowapi`.
- `api/app/telegram/webhook.py`, `api/app/main.py` (changed): limiter set-up and the `429` handler.
- `api/tests/test_telegram_rate_limit.py` (new).

**Rules**

- Limit: `120/minute` per client address, on the webhook route only. Telegram's own delivery to one bot stays far below this.
- Over the limit → `429` with `Retry-After`. Telegram retries later, and the idempotency check (BE-012) makes that safe.
- In-memory storage (single API process). Note in the code: move to the Redis storage backend when the API runs more than one process.
- Behind ngrok all requests arrive from the tunnel's address, so the limit is effectively global in dev. That is acceptable and stated in a comment.
- The limit is a named constant, overridable by the `TELEGRAM_WEBHOOK_RATE_LIMIT` setting so tests can set it to `3/minute`.

## Steps

1. Check `slowapi` on PyPI again; add it.
2. Wire the limiter to the one route.
3. Tests with a low limit.

## Tests

- `test_requests_under_limit_pass`
- `test_request_over_limit_is_429_with_retry_after`
- `test_limit_applies_before_secret_check_result_matters`: wrong-secret requests also count.
- `test_other_routes_are_not_limited`

## Acceptance criteria

- [ ] The webhook returns `429` over the limit
- [ ] Requests with a wrong secret count towards the limit
- [ ] No other route is affected
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. Where the limiter is attached: one route.
2. Wrong-secret requests are counted (otherwise guessing is unlimited).

Things that should *not* be in the diff: limits on protected routes; Redis storage.

## Out of scope

- Multi-process storage → when deployment is decided.

## Notes / log

The agent adds progress notes, decisions and open questions here.
