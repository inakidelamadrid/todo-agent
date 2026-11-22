# BE-015: Handler registry and dispatch from the webhook

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §2, §5.2
- **Assigned agent / harness / model:**
- **Depends on:** BE-012, BE-013
- **Can run in parallel with:** none
- **Public endpoint?** yes (same route as BE-008)
- **Review size:** ~90 lines, 3 files, ~12 min

## Goal

The webhook runs the handler registered for the update's route target, and falls back to a placeholder when no feature has registered one yet.

## Why this ticket exists

This is the seam the other epics plug into. A feature adds one line to a dictionary; it never edits the webhook. The placeholder means every command in the list is routable today, even though most features do not exist.

## Read first

- `api/app/telegram/routing.py`.
- `api/app/telegram/webhook.py` as left by BE-012.
- A *port* is the function signature the rest of the app agrees on; an *adapter* is one function that satisfies it. Here the port is `Handler`.

## Design

- **Pattern:** Ports and adapters: `Handler` is the port, each feature supplies an adapter, and a dictionary is the registry.
- **Data flow:** `Route.target` → `resolve(target)` → `handler(update, route, ctx)` → `Reply | None` → `mark_update`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/handlers.py` (new).
- `api/app/telegram/webhook.py` (changed).
- `api/tests/test_telegram_handlers.py` (new).

**Types**

```python
class Reply(BaseModel):                 # frozen; what a handler wants said back
    template: str                       # a template name (BE-020)
    data: Mapping[str, str] = {}

@dataclass(frozen=True)
class HandlerContext:
    session: AsyncSession
    now: datetime                       # aware, UTC; passed in so handlers stay testable

Handler = Callable[[InboundUpdate, Route, HandlerContext], Awaitable[Reply | None]]
```

**Registry**

- `HANDLERS: Mapping[str, Handler]`: starts with `core.help`, `core.unknown_command`, `core.unsupported`, each returning a `Reply` naming a template of the same name without the `core.` prefix (`help`, `unknown_command`, `unsupported`).
- `async def not_available(update, route, ctx) -> Reply`: returns `Reply(template="not_available")`.
- `def resolve(target: str) -> Handler`: `HANDLERS.get(target, not_available)`.

**Webhook.** Between claim and mark:

```python
route = routing.route(update)
try:
    reply = await handlers.resolve(route.target)(update, route, ctx)
    status = "processed"
except Exception:
    logger.exception("telegram.handler_failed")   # no update content in the message
    status = "failed"
await repository.mark_update(session, update.update_id, status, route.target)
```

The response is `200` either way: a failing handler must not make Telegram retry into the same failure. `reply` is computed and dropped for now; BE-021 sends it.

## Steps

1. Define the types and the three core handlers.
2. Add `resolve` and `not_available`.
3. Call them from the webhook.
4. Tests.

## Tests

- `test_resolve_returns_registered_handler`
- `test_resolve_falls_back_to_not_available`
- `test_help_handler_replies_with_help_template`
- `test_webhook_records_route_target`: after `command.json`, the row's `route` is `core.help`.
- `test_failing_handler_marks_failed_and_returns_200`: registry patched with a handler that raises.

## Acceptance criteria

- [ ] Adding a feature command requires one entry in `HANDLERS` and no webhook change
- [ ] An unregistered target runs `not_available`
- [ ] A handler exception yields `status = failed` and a `200`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Post `command.json` with curl (see BE-008), then `select update_id, route, status from telegram_updates;` shows `core.help`, `processed`.

## Review guide

Read the diff in this order, and check:

1. `handlers.py`: the `Handler` signature. Could a feature author implement it knowing nothing about Telegram?
2. `webhook.py`: the `try` wraps only the handler call.
3. The exception log has no message content.

Things that should *not* be in the diff: sending messages; feature logic for `/now`, `/vault`, etc.

## Out of scope

- Sending the reply → BE-021.
- Session state in the context → BE-016.
- Feature handlers → their own epics.

## Notes / log

The agent adds progress notes, decisions and open questions here.
