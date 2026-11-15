# Patterns to reach for

The house style is functional: pure functions in the core, side effects at the edges, immutable data, composition over inheritance. Classic design patterns still apply, in their function-shaped form. Name the pattern in the ticket so the reviewer knows what shape to expect, and point at where the codebase already does it.

Pick the simplest thing that works. A pattern earns its place only when the ticket has the problem the pattern solves.

## Structural

| Pattern | Use when | Functional form here |
|---|---|---|
| **Functional core, imperative shell** | Always, as the default layering | Rules live in pure modules (`api/app/bills/domain.py`, `web/.../model/schedule.ts`); I/O lives in `repository.py`, `router.py`, `api/client.ts`, the store |
| **Repository** | Reading or writing the database | Module of async functions taking a session, one operation each (`api/app/bills/repository.py`). No repository classes |
| **Thin controller** | Any route | validate → call repository/domain → return schema (`api/app/bills/router.py`) |
| **Dependency injection** | A route needs a session, the current key/user, settings, or a swappable service | FastAPI `Depends`; tests override the dependency instead of patching |
| **Ports and adapters** | Talking to anything external (Telegram, email, Drive, AI) or merging several sources (the radar) | The port is a function type (`Protocol` / TS function type); each adapter is a function that satisfies it; a fake adapter ships first for tests |
| **Anti-corruption layer** | An external payload has its own vocabulary | One mapping function at the edge turns it into our types; nothing past the edge sees the foreign shape |
| **Facade** | Several low-level calls always go together | One function that composes them, e.g. a single `request()` helper under the typed client functions |

## Behavioural

| Pattern | Use when | Functional form here |
|---|---|---|
| **Strategy** | Behaviour varies by type (reminder stages per item type, recurrence rules) | A `dict` / `Record` from the discriminator to a function, instead of `if` chains or subclasses |
| **State transitions (reducer)** | UI or domain state changes in named steps | Pure `(state, input) → newState` functions (`web/.../model/transitions.ts`); the store only calls them |
| **State machine** | A record has a lifecycle with illegal moves (ticket status, signature pending → signed) | A transition table plus one pure `transition(state, event)` that returns the new state or an error |
| **Pipeline / composition** | Data flows through several steps (parse → validate → enrich → persist) | Small functions composed in order; each step testable alone |
| **Command** | An action must be queued, retried or logged (outbound messages, jobs) | A frozen data object describing the action, plus a handler function |
| **Observer / pub-sub** | One event has several independent reactions | Zustand selectors on the frontend; a queue on the backend. Avoid in-process event buses unless the ticket needs one |
| **Specification / predicate** | A rule is reused in filters and validation | A named pure predicate (`is_due_in_month`), combined with `and`/`or` |

## Data and errors

| Pattern | Use when | Functional form here |
|---|---|---|
| **Parse, don't validate** | Data crosses a boundary | Parse once at the edge into a typed, trusted value (Pydantic model, or a schema parser on the frontend); the core never re-checks |
| **Immutable value objects** | Any domain data | Frozen Pydantic models / dataclasses; `readonly` TS types; return new values |
| **Discriminated union** | A value is one of several shapes (`RadarItem` by source, request status) | `Literal`-tagged Pydantic union; TS union with a `kind` field and exhaustive `switch` |
| **Result over exceptions** | A failure is an expected outcome of pure logic | Return `value \| None` or a small tagged result; raise only at the edge (`HTTPException`, typed `ApiError`) |
| **Null object / safe default** | Absence is normal | Empty list, `""`, zero cents, rather than `None` checks spread around |

## Reliability and integration

| Pattern | Use when | Functional form here |
|---|---|---|
| **Idempotent upsert** | A client or webhook may repeat a request | `PUT` keyed by natural id, as payments are by `(billId, period)` |
| **Idempotency key** | Webhooks and bots deliver twice | Store the provider's update id; a repeated id is a no-op |
| **Optimistic update with rollback** | A user action should feel instant | Apply the pure transition, call the API, restore the previous state on failure (FE-001's store) |
| **Outbox / queue** | Sending must survive a crash and respect caps and quiet hours | Persist the command, let a worker send it; one policy function decides whether to send now |
| **Retry with backoff** | An external call can fail transiently | A library decorator, not a hand-written loop |
| **Signature / token guard** | A public endpoint (webhook, signing page) | A shared dependency that verifies in constant time; never an inline check in the route |

## Frontend composition

| Pattern | Use when | Form here |
|---|---|---|
| **Presentational vs connected components** | Every screen | Presentational components take props and render all states; one thin component connects them to the store. Each is its own ticket |
| **Custom hook** | Stateful logic is reused or clutters a component | `useX` returning data and actions; the logic inside stays in pure functions |
| **Compound components** | A widget has cooperating parts | Follow shadcn/ui's composition (`Sheet`, `SheetContent`, …) rather than a prop-heavy single component |
| **Selector** | A component needs a slice of the store | Narrow Zustand selectors to avoid re-renders |

## Smells that mean "split or simplify the ticket"

- A class with methods where a module of functions would do.
- Inheritance for reuse.
- A function that both computes and performs I/O.
- An abstraction with one implementation and no test fake.
- A "utils" or "helpers" file gaining unrelated functions.
- The same rule implemented separately on both sides without paired tickets.
