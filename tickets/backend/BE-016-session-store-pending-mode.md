# BE-016: Session store port and pending mode in the router

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Router step 3, §6
- **Assigned agent / harness / model:**
- **Depends on:** BE-015
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~100 lines, 4 files, ~15 min

## Goal

A feature can say "the next photo from this chat is mine", and the router honours it once.

## Why this ticket exists

After `/vault` the user sends a photo with no caption; without memory the bot would ask what it is. That memory is short-lived session state. This ticket defines the port and an in-memory implementation, so the routing rule can be reviewed and tested before Redis is involved.

## Read first

- `api/app/telegram/routing.py`, `handlers.py`.
- House style has no service classes. A port with several operations is a frozen dataclass whose fields are functions; a factory function builds one by closing over its state.

## Design

- **Pattern:** Port + fake: the port is a frozen dataclass of functions; the in-memory version doubles as the test fake.
- **Data flow:** webhook → `store.get(chat_id)` → `route(update, pending_mode)` → on a `pending` route, `store.clear(chat_id)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/sessions.py` (new).
- `api/app/telegram/routing.py` (changed): `route` gains `pending_mode`.
- `api/app/telegram/handlers.py`, `webhook.py` (changed): context and wiring.
- `api/tests/test_telegram_sessions.py` (new).

**Types**

```python
class PendingSession(BaseModel):        # frozen
    mode: str                           # e.g. "vault"
    context: Mapping[str, str] = {}

@dataclass(frozen=True)
class SessionStore:
    get: Callable[[int], Awaitable[PendingSession | None]]             # chat_id
    set: Callable[[int, PendingSession, int], Awaitable[None]]         # chat_id, session, ttl_seconds
    clear: Callable[[int], Awaitable[None]]

DEFAULT_SESSION_TTL_SECONDS = 600
```

- `in_memory_session_store(clock: Callable[[], float] = time.monotonic) -> SessionStore`: a dict in a closure; honours the TTL using `clock`.
- `get_session_store(request: Request) -> SessionStore`: dependency returning `request.app.state.session_store`, created in the lifespan.

**Routing**

```python
PENDING_ACCEPTS: Mapping[str, tuple[frozenset[UpdateKind], str]] = {
    "vault": (frozenset({UpdateKind.PHOTO, UpdateKind.DOCUMENT}), "vault.store"),
}

def route(update: InboundUpdate, pending_mode: str | None = None) -> Route
```

New step 3, after callbacks and commands, before keywords: if `pending_mode` is in `PENDING_ACCEPTS` and `update.kind` is accepted → `Route("pending", target)`.

**Webhook.** Read the session before routing; when the route kind is `pending`, clear it (one use). `HandlerContext` gains `sessions: SessionStore`, so a handler such as `/vault` can call `ctx.sessions.set(...)`.

## Steps

1. Write the port and the in-memory store with TTL tests.
2. Extend `route` and its tests.
3. Wire the webhook and the context.

## Tests

- `test_in_memory_store_round_trip`
- `test_session_expires_after_ttl` (fake clock)
- `test_clear_removes_session`
- `test_pending_vault_routes_next_photo_to_vault`
- `test_pending_mode_ignores_text`: text still goes to the brain dump.
- `test_command_wins_over_pending_mode`
- `test_webhook_clears_pending_mode_after_use`: set vault mode, post `photo.json` without caption twice; the second routes to `media.classify`.

## Acceptance criteria

- [ ] `route` stays pure: the pending mode is an argument, not something it fetches
- [ ] A pending mode is consumed exactly once and expires after its TTL
- [ ] Nothing imports Redis
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `sessions.py`: the port is three functions; the in-memory store has no hidden global.
2. `routing.py`: where step 3 sits relative to commands and keywords.
3. `webhook.py`: the clear happens only for `pending` routes.

Things that should *not* be in the diff: a Redis client; the `/vault` handler (EPIC-006).

## Out of scope

- Redis-backed store → BE-017.
- The handler that sets vault mode → EPIC-006.

## Assumptions

- Session TTL is 10 minutes (the epic says "a TTL").

## Notes / log

The agent adds progress notes, decisions and open questions here.
