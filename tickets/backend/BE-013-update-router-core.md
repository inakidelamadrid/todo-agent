# BE-013: Router: callback, command and default routes

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Router steps 1, 2, 5
- **Assigned agent / harness / model:**
- **Depends on:** BE-006
- **Can run in parallel with:** BE-007 to BE-012
- **Public endpoint?** no
- **Review size:** ~120 lines, 2 files, ~15 min

## Goal

A pure function decides where an update goes: a callback action, a command's feature, or the brain dump by default.

## Why this ticket exists

The epic asks for "one routing table, easy to extend when a new epic adds a command". That is a dictionary plus one function, with no I/O, so it can be tested exhaustively with the recorded payloads. Pending mode and keywords are added by the next two tickets so this one stays readable.

## Read first

- `api/app/bills/domain.py`: pure functions with no framework imports.
- `web/src/features/bills/model/transitions.ts`: the same idea on the frontend.
- Naming: `api/app/telegram/webhook.py` is the FastAPI route; this new `routing.py` is the pure decision. "Router" in the epic means this one.

## Design

- **Pattern:** Strategy as a dictionary (command → target) plus a tagged result (`Route.kind`), instead of an `if` chain per command.
- **Data flow:** `InboundUpdate` → `route(update)` → `Route`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/routing.py` (new).
- `api/tests/test_telegram_routing.py` (new).

**Types**

```python
RouteKind = Literal["callback", "command", "pending", "keyword", "default", "unsupported"]

class Route(BaseModel):   # frozen
    kind: RouteKind
    target: str           # "<feature>.<action>", e.g. "core.help"
    arg: str = ""         # callback argument (filled by BE-023)
```

**Command table** (the single place a new command is added):

| Command | Target | Owner |
|---|---|---|
| `help` | `core.help` | this epic |
| `start` | `core.start` | BE-046 |
| `undo` | `core.undo` | later |
| `pause` | `notifications.pause` | BE-028 |
| `resume` | `notifications.resume` | BE-028 |
| `now` | `tasks.now` | EPIC-003 |
| `inbox` | `inbox.count` | EPIC-003 |
| `done` | `tasks.done` | EPIC-003 |
| `today` | `expenses.today` | EPIC-002 |
| `month` | `expenses.month` | EPIC-002 |
| `radar` | `radar.show` | EPIC-004 |
| `reset` | `reset.start` | EPIC-005 |
| `vault` | `vault.await_upload` | EPIC-006 |

`COMMANDS: Mapping[str, str]` holds it, wrapped in `MappingProxyType` so it cannot be mutated.

**Function (pure)**

```python
def route(update: InboundUpdate) -> Route
```

In this order:

1. `CALLBACK` → `Route(kind="callback", target="callback.unverified")`. BE-023 replaces the target with the verified action.
2. `COMMAND` → `Route("command", COMMANDS[cmd])`, or `Route("command", "core.unknown_command")`.
3. `TEXT`, `VOICE` → `Route("default", "braindump.capture")`.
4. `PHOTO`, `DOCUMENT` → `Route("default", "media.classify")`.
5. `UNSUPPORTED` → `Route("unsupported", "core.unsupported")`.

## Steps

1. Define `Route` and `COMMANDS`.
2. Write `route` branch by branch with a test each.

## Tests

- `test_every_listed_command_routes_to_its_target` (parametrised over `COMMANDS`).
- `test_unknown_command_routes_to_unknown_command`
- `test_text_and_voice_default_to_braindump`
- `test_photo_and_document_default_to_classify`
- `test_callback_wins_over_everything`
- `test_unsupported_update`
- `test_commands_table_is_immutable`

## Acceptance criteria

- [ ] All 13 commands from the epic's list (plus `start`) are in `COMMANDS`
- [ ] `route` is pure: no I/O, no settings, no clock
- [ ] Every fixture from BE-005 has a routing test
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `COMMANDS`: compare with the epic's command list (§5.1).
2. `route`: can you predict the result for each fixture by reading it top to bottom?

Things that should *not* be in the diff: FastAPI imports, database access, handler functions.

## Out of scope

- Caption keywords → BE-014.
- Pending mode → BE-016.
- Running the handler for a target → BE-015.
- Verifying callback data → BE-023.

## Notes / log

The agent adds progress notes, decisions and open questions here.
