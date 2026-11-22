# BE-073: `explain_route`: the router's decision, step by step, as a pure function

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-009, BE-013
- **Can run in parallel with:** BE-072, BE-077
- **Public endpoint?** no
- **Review size:** ~80 lines, 2 files plus tests, ~12 min

## Goal

`explain_route(update, allowed_user_id, already_seen)` returns the ordered steps the webhook would take for an update and the final route, without doing any of them.

## Why this ticket exists

This is the tool that answers 'why did the bot do that?'. It must call the same pure functions the webhook calls (`is_allowed`, `routing.route`), so the explanation can never disagree with the real behaviour.

## Read first

- `api/app/telegram/allowlist.py` (BE-009): `is_allowed`.
- `api/app/telegram/routing.py` (BE-013, and BE-014/BE-016 if merged): `route` and its order.
- `api/app/telegram/webhook.py`: the real order of checks.

## Design

- **Pattern:** Result as a value: a frozen `RouteExplanation` built by composing the existing pure functions. No I/O.
- **Data flow:** `InboundUpdate` → `is_allowed` → idempotency verdict (given) → `routing.route` → `RouteExplanation`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/playground/explain.py` (new).
- `api/app/telegram/playground/schemas.py` (changed): the response types, camelCase.

```python
class ExplainStep(BaseModel):     # frozen
    name: Literal["allowlist", "idempotency", "route"]
    verdict: Literal["pass", "stop", "skipped"]
    detail: str                   # fixed wording from a small table, never update content

class RouteExplanation(BaseModel):   # frozen
    steps: tuple[ExplainStep, ...]
    final_route: Route | None        # None when a step stopped it

def explain_route(update: InboundUpdate, *, allowed_user_id: int | None, already_seen: bool) -> RouteExplanation
```

**Steps, in the webhook's order**

1. `allowlist`: `is_allowed(update, allowed_user_id)`. False → `stop`, detail 'Not from the allowed account: ignored silently'. Later steps `skipped`.
2. `idempotency`: `already_seen` → `stop`, 'Already processed: acknowledged, nothing runs'. Else `pass`.
3. `route`: `routing.route(update)`; `pass`, detail names the rule that matched by `route.kind` ('command table', 'default: text goes to the brain dump', 'caption keyword', 'pending mode', 'unsupported').

The secret-token check is not a step: the playground is not the webhook and has its own guards.

If the router gained rules since this ticket was written (keywords BE-014, pending mode BE-016), the explanation reflects them automatically because it calls `route`; only the wording table needs a line.

## Steps

1. Types.
2. Function, one step at a time with its tests.
3. Run `make api-test`.

## Tests

- `test_allowed_new_command_explains_three_passes_and_the_route`.
- `test_stranger_stops_at_allowlist_and_skips_the_rest`.
- `test_duplicate_stops_at_idempotency`.
- `test_unknown_command_routes_to_core_unknown_command`.
- `test_text_routes_to_default`.
- `test_explanation_matches_router_for_every_recorded_fixture`: for each fixture, `final_route == routing.route(to_inbound(fixture))`.
- `test_details_never_contain_update_text`.

## Acceptance criteria

- [ ] `explain_route` is pure and calls `is_allowed` and `routing.route`, not copies of them
- [ ] For every recorded fixture the final route equals the real router's
- [ ] A stopped step skips the later ones
- [ ] No detail string contains update content
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_playground_explain.py -q`: green.

## Review guide

Read the diff in this order, and check:

1. `explain.py`: is any routing rule re-implemented here? None should be.
2. Is the step order the webhook's order?

Things that should *not* be in the diff: Database reads, handlers, routes.

## Out of scope

- The endpoint → BE-074.
- Executing the handler → BE-076.

## Notes / log

The agent adds progress notes, decisions and open questions here.
