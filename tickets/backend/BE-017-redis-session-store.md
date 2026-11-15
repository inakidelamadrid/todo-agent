# BE-017: Redis client and Redis-backed session store

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §6
- **Assigned agent / harness / model:**
- **Depends on:** BE-016
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 5 files, ~12 min

## Goal

Pending sessions live in Redis with a real TTL, so they survive an API restart and expire on their own.

## Why this ticket exists

The Redis container has run since BE-002 but the API has never talked to it. This ticket adds the client once, behind a dependency, and swaps the session store's implementation without touching the router or the webhook: the port from BE-016 pays off here.

## Read first

- `api/app/db.py` and the lifespan in `api/app/main.py`: how the Postgres engine is created once and disposed.
- `.env.db.example`: `REDIS_PASSWORD`, `REDIS_PORT` already exist.
- https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
- Redis `SET key value EX seconds` stores a value that Redis deletes by itself after the TTL.

## Design

- **Pattern:** Adapter behind the `SessionStore` port; the client is injected with a FastAPI dependency.
- **Data flow:** lifespan → `build_redis(settings)` → `app.state.redis` → `redis_session_store(client)` → `app.state.session_store`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `redis` | **new** | Async Redis client (`redis.asyncio`) | 8.1.0, MIT, released 2026-07-30, Python ≥3.10. It is the official client and includes asyncio support; the older `aioredis` was merged into it. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add redis`.
- `api/app/settings.py` (changed): `redis_host: str = "127.0.0.1"`, `redis_port: int = 6379`, `redis_password: SecretStr = SecretStr("")` (read from `../.env.db` like the Postgres values).
- `api/app/redis.py` (new): `build_redis(settings) -> Redis` (`decode_responses=True`), `async close_redis(client)`, `get_redis(request) -> Redis`.
- `api/app/telegram/sessions.py` (changed): `redis_session_store(client: Redis) -> SessionStore`.
- `api/app/main.py` (changed): build and close the client in the lifespan; use the Redis store.
- `api/tests/test_telegram_sessions_redis.py` (new).

**Storage**

- Key: `tg:session:<chat_id>`. Value: `PendingSession.model_dump_json()`.
- `set` → `SET key value EX ttl_seconds`. `get` → parse, or `None` when missing or unparseable. `clear` → `DEL`.

**Tests** run against the Docker Redis. Each xdist worker uses its own key prefix (`test:<worker_id>:`) and deletes its keys afterwards. If Redis is down, fail loudly with "run `make db-up`", as the Postgres fixtures do.

## Steps

1. Check `redis` on PyPI again; `uv add redis`.
2. Add the settings and `api/app/redis.py`.
3. Write the adapter.
4. Switch the lifespan to it.
5. Tests.

## Tests

- `test_redis_store_round_trip`
- `test_redis_store_sets_ttl`: `TTL key` is between 1 and the requested seconds.
- `test_redis_store_clear`
- `test_unparseable_value_reads_as_none`
- `test_redis_password_not_in_repr`

## Acceptance criteria

- [ ] `redis` is a runtime dependency
- [ ] The webhook tests from BE-016 pass unchanged against the Redis store
- [ ] The Redis password is a `SecretStr` and is never logged
- [ ] The client is created once and closed on shutdown
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make db-up
```

```bash
make api-test
```

Optionally `make db-redis-cli`, then `keys tg:*` after setting a session in a test with a breakpoint.

## Review guide

Read the diff in this order, and check:

1. `api/app/redis.py`: one client, built from settings, closed in the lifespan.
2. `redis_session_store`: three small functions; the TTL is passed to Redis, not tracked by us.
3. No change in `routing.py` or the webhook's logic.

Things that should *not* be in the diff: queues, rate limiting, caching of anything else.

## Out of scope

- Outbound queue → BE-029 to BE-031.
- Pending media references → BE-045.

## Notes / log

The agent adds progress notes, decisions and open questions here.
