# EPIC-003 Phase 1 outline: core loop

Proposed breakdown of [EPIC-003: Brain-dump inbox + "What now?"](../Epics/EPIC-003-brain-dump-inbox-what-now.md), Phase 1 only: self-hosted n8n, tasks, dumps + inbox, web Quick add, Inbox triage, What now? (rules engine) and the focus timer. Tickets are written (56 files: BE-080–113, FE-031–052); this outline is their map.

## How this is chunked

Development comes in **milestones you can try yourself**. Each one ends with a **Demo**: something you run, click or curl to see the new behaviour working, not just green tests. Inside a milestone, every ticket has its own **Human check**, so even a pure-function ticket gives you something to poke at (a REPL line, a named test, a `/docs` call).

Rules:

- A milestone is done when its demo works on your machine.
- No milestone depends only on tests: each one adds something visible in the browser, `/docs`, `curl` or `make`.
- Backend tickets come before the frontend tickets that use them inside the same milestone, so the demo always runs against the real API.
- The inbox works **without n8n** first (a fallback keeps the raw text as one item). Real AI splitting is its own milestone, so a blocked EPIC-008 ticket never stops the fun.

## Milestones at a glance

| M | Milestone | Tickets | Demo |
|---|---|---|---|
| 1 | n8n runs locally | BE-109–111 | `make n8n-up && make n8n-check` → ✓; n8n opens at `http://127.0.0.1:5678` |
| 2 | Tasks through the API | BE-080–088 | In `/docs`: create a task, list it, complete it, reopen it |
| 3 | Tasks in the browser | FE-040, FE-031, FE-032, FE-051, FE-052 | `#tasks` shows your tasks; Done and Let go work |
| 4 | Brain dump through the API | BE-089, BE-090, BE-092–096, BE-113 | `curl POST /inbox/dumps` → `GET /inbox` shows your raw text as an item |
| 5 | Quick add and Inbox in the browser | FE-033, FE-035–039, FE-041 | Press `/`, type a thought, it appears in `#inbox` |
| 6 | Accept and let go | BE-097, BE-098, FE-034 | Accept an inbox item → it shows up in `#tasks` |
| 7 | Edit, snooze, accept all | BE-099, BE-100, FE-042–044 | Edit before accepting; snooze to tomorrow; Accept all |
| 8 | Real AI splitting | BE-091, BE-112 | `call dentist next week, also buy cat food` → two task items in `#inbox` |
| 9 | What now? through the API | BE-101–106 | `POST /now` in `/docs` → one task plus a readable *why* |
| 10 | What now? in the browser | FE-045–048 | Press `n`, answer two chips, get one task; Another, Not today |
| 11 | Focus timer | BE-107, BE-108, FE-049, FE-050 | Start → countdown → Done marks the task done |

M1 can run any time. M8 is blocked on EPIC-008 (see Blocked); M9–M11 don't need it.

## M1: n8n runs locally ([n8n-io/n8n](https://github.com/n8n-io/n8n))

**Demo:** `make n8n-up`, then `make n8n-check` prints ✓ for health, readiness and `N8N_BASE_URL`. Open `http://127.0.0.1:5678` and create the owner account by following the runbook.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 1 | BE-109 | n8n service in `docker-compose.yml`: pinned `n8nio/n8n` image (2.48.7 checked on Docker Hub 2026-11-22; check again when building), `n8n` compose profile, bound to `127.0.0.1:5678`, `n8n_data` volume, SQLite, healthcheck, `.env.n8n.example` (`N8N_ENCRYPTION_KEY`, `GENERIC_TIMEZONE=America/Mexico_City`, telemetry off, env access blocked in Code nodes) | none | — | Docker image `n8nio/n8n` | 60 | `docker compose --profile n8n up -d n8n` → healthy in `docker compose ps`; `make db-up` alone doesn't start it |
| 2 | BE-110 | Make targets: `n8n-up` (env guard, waits until healthy), `n8n-down`, `n8n-status`, `n8n-logs`, `n8n-check` (`/healthz` + `/healthz/readiness`, plus whether `N8N_BASE_URL` in `api/.env` points at it; prints ✓/✗, never a secret) | BE-109 | — | — | 70 | `make n8n-up`, `make n8n-check` ✓; `make n8n-down` then `make n8n-check` ✗ with a hint |
| 3 | BE-111 | `RUNBOOK-n8n-setup.md`: first-run owner account, HMAC secret as an n8n credential, import/export of `integrations/n8n/workflows/`, backup with `n8n export:*`, upgrade steps, licence note | BE-110 | — | — | 120 (docs) | Follow it start to finish on a clean volume; you end signed in with the credential created |

## M2: Tasks through the API

**Demo:** in `http://127.0.0.1:8000/docs` (signed-in token or API key): `POST /tasks` "Call dentist" size S → `GET /tasks` lists it → `POST /tasks/{id}/complete` → status `done` → `/reopen` → `active`. A subtask of a subtask returns `422`.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 4 | BE-080 | Task schemas: size, energy, context, status enums; Create/Update/Out | none | Parse, don't validate | — | 110 | REPL: `TaskCreate(title="  x  ", size="S")` trims the title; `size="XXL"` raises a `ValidationError` |
| 5 | BE-081 | Task status state machine plus size→minutes rules (pure) | BE-080 | State machine | — | 90 | REPL: `transition("done", "snooze")` returns an error; `size_minutes("M") == 45` |
| 6 | BE-082 | `tasks` table plus migration (one-level `parentId`, checks) | BE-080 | — | — | 90 | `make api-migrate`, then `\d tasks` in `make db-psql` shows the columns and checks |
| 7 | BE-083 | Task repository: list and get | BE-082 | Repository | — | 50 | `make api-test -- -k task_repository` shows the named tests passing |
| 8 | BE-084 | Task repository: create, update, delete; blocks subtasks deeper than one level | BE-083 | Repository | — | 80 | Named tests, including `test_rejects_grandchild_task` |
| 9 | BE-085 | `GET /tasks` (status filter) and `GET /tasks/{id}` | BE-084 | Thin controller | — | 90 | `/docs`: `GET /tasks` → `200 []`; no credentials → `401` |
| 10 | BE-086 | `POST /tasks` | BE-085 | Thin controller | — | 70 | `/docs`: create one, then see it in `GET /tasks` |
| 11 | BE-087 | `PATCH` and `DELETE /tasks/{id}` | BE-086 | Thin controller | — | 80 | `/docs`: rename it, delete it, `GET` → `404` |
| 12 | BE-088 | `POST /tasks/{id}/complete`, `/snooze`, `/drop`, `/reopen` | BE-081, BE-087 | State machine | — | 100 | `/docs`: complete → `done`; complete again → `409` |

## M3: Tasks in the browser

**Demo:** `make web-dev`, open `#tasks`: the tasks from M2 are grouped by do date, "past its date" is shown calmly, and Done and Let go update the list (and survive a reload).

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 13 | FE-040 | Refactor: data-driven screen registry in `screen.ts` and `App.tsx` (no behaviour change) | none | Strategy | — | 70 | Bills and Playground still switch exactly as before |
| 14 | FE-031 | Task types plus pure model (size labels, calm "past its date" wording) | BE-080 | Value objects | — | 100 | `npm --prefix web test -- tasks/model` passes; read the wording table in the test |
| 15 | FE-032 | Tasks API client | FE-031, BE-088 | Facade over `request()` | — | 90 | Named client tests pass; in the browser console, `listTasks()` returns the M2 tasks |
| 16 | FE-051 | Task list (active tasks by do date; Done, Let go), fixture data | FE-031, FE-040 | Presentational | — | 140 | Temporary fixture route: every state (loading, empty, error, past its date) at desktop and phone width |
| 17 | FE-052 | Wire the task list plus its `#tasks` nav item | FE-032, FE-040, FE-051 | Connected component | — | 130 | M3 demo |

## M4: Brain dump through the API

**Demo:** with n8n **not** configured: `curl -X POST /inbox/dumps -d '{"rawText":"call dentist, buy cat food","source":"web"}'` → `201` with one fallback item holding your text; `GET /inbox` lists it. The raw dump is saved.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 18 | BE-089 | Inbox schemas: `DumpIn`, the candidate item union by `type`, `InboxItemOut` | BE-080 | Discriminated union | — | 120 | REPL: a `task` payload with an `amountCents` field is rejected; an empty `rawText` raises an error |
| 19 | BE-090 | `DumpParser` port owned by the inbox (`parse(raw_text, today) -> ParseDumpResult`), strict result schema, a fake and `unconfigured_parser` | BE-089 | Ports and adapters | — | 90 | REPL: `await fake_parser(...)("x", date.today())` returns the canned items |
| 20 | BE-092 | `dumps` and `inbox_items` tables plus migration | BE-089 | — | — | 100 | `make api-migrate`; `\d inbox_items` shows the FK to `dumps` with cascade |
| 21 | BE-093 | Pure mapping from parse result to item drafts, plus `today_in(tz, now)` | BE-090 | Anti-corruption layer | — | 90 | REPL: `today_in("America/Mexico_City", <UTC 03:00>)` returns yesterday's date |
| 22 | BE-094 | Inbox repository: save a dump with its items, list new items, get one | BE-092, BE-093 | Repository | — | 80 | Named repository tests pass |
| 23 | BE-095 | `POST /inbox/dumps` (keeps the raw text as a fallback item when the parser fails or isn't configured) | BE-093, BE-094 | Pipeline | — | 110 | `curl` from the demo → `201`; no credentials → `401` |
| 24 | BE-096 | `GET /inbox` (newest first, hides snoozed) | BE-094 | Thin controller | — | 60 | M4 demo |
| 24a | BE-113 | Dev-only splitter parser behind `DUMP_PARSER=dev` (refused in production), so M5–M7 show several confident items without n8n | BE-090, BE-095 | Ports and adapters (second adapter) | — | 70 | `DUMP_PARSER=dev`, then the M4 `curl` with `call dentist, also buy cat food and also pay gym 600` → three items |

## M5: Quick add and Inbox in the browser

**Demo:** from any screen, press `/`, type two lines, press ⌘↵ → toast "In your inbox". Open `#inbox`: the item shows its original text and a confidence indicator. Delete everything in the DB → the calm inbox-zero state appears.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 25 | FE-033 | Inbox types plus API client (`postDump`, `listInbox`) | BE-096 | Discriminated union | — | 90 | Named client tests pass; `listInbox()` in the console returns the M4 item |
| 26 | FE-035 | Pure `shouldHandleShortcut` plus `useShortcut` hook | none | Custom hook | — | 60 | Tests show `/` is ignored while typing in an input |
| 27 | FE-036 | Quick add field (presentational, multi-line, all states), fixture data | FE-040 | Presentational | — | 110 | Fixture route: idle, typing, sending, error, focus ring at desktop and phone width |
| 28 | FE-037 | Wire Quick add: `/` shortcut, `POST /inbox/dumps`, toast | FE-033, FE-035, FE-036 | Connected component | — | 80 | Press `/`, send a dump, then `GET /inbox` in `/docs` shows it |
| 29 | FE-038 | Inbox item card: confidence, original text; action buttons shown only when handlers are passed | FE-033, FE-040 | Presentational | — | 140 | Fixture route: high- and low-confidence cards, each item type, hover and focus |
| 30 | FE-039 | Inbox list: loading, error and calm inbox-zero states | FE-038 | Presentational | — | 110 | Fixture route: all four states |
| 31 | FE-041 | Wire the Inbox screen (read-only) plus its `#inbox` nav item | FE-033, FE-039, FE-040 | Connected component | — | 80 | M5 demo |

## M6: Accept and let go

**Demo:** in `#inbox`, Accept a task item → it disappears from the inbox and appears in `#tasks` with its size and first step. Let go of another → gone, and the raw dump is still in the DB. Kill the API and click Accept → the card comes back with a calm error.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 32 | BE-097 | Pure `task_from_item(item, edits)` | BE-081, BE-089 | Plain function | — | 70 | REPL: a reminder item becomes a task with `dueDate` set |
| 33 | BE-098 | `POST /inbox/{id}/accept` (with edits) and `/discard` | BE-084, BE-096, BE-097 | Thin controller | — | 110 | `/docs`: accept → `GET /tasks` shows the task; accepting a `note` → `409` |
| 34 | FE-034 | Inbox actions client plus store: accept and let go, optimistic with rollback; wires the card's buttons | FE-033, FE-041, BE-098 | Reducer plus optimistic rollback | — | 140 | M6 demo |

## M7: Edit, snooze, accept all

**Demo:** edit an item's title and size before accepting; snooze one to "Tomorrow" (it vanishes, and `GET /inbox` still hides it); dump three high-confidence items and use Accept all.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 35 | BE-099 | Pure `snooze_until(option, now)` plus `POST /inbox/{id}/snooze` | BE-093, BE-098 | Strategy (option → function) | — | 100 | REPL: `snooze_until("tomorrow", now)` is 08:00 tomorrow Mexico City time; `/docs` snooze → hidden from `GET /inbox` |
| 36 | BE-100 | `POST /inbox/accept-all?minConfidence=` | BE-098 | Specification | — | 80 | `/docs`: three items, threshold 0.8 → only the confident ones become tasks |
| 37 | FE-042 | Edit-before-accept sheet | FE-034 | Compound components (Sheet) | — | 150 | Open, edit, accept → the task has the edited values; Esc closes; phone width |
| 38 | FE-043 | Snooze client plus popover (later today, tomorrow, next week, date) | FE-034, BE-099 | Presentational | — | 100 | Snooze → item leaves the list; keyboard-only works |
| 39 | FE-044 | Accept all above the threshold (client plus button) | FE-034, BE-100 | — | — | 70 | M7 demo |

## M8: Real AI splitting

**Demo:** with `make n8n-up` and the workflow imported: Quick add `call dentist next week, also buy cat food and pay gym 600` → three items in `#inbox` (two tasks, one expense) with dates resolved in Mexico City. Stop n8n → the next dump still lands as one fallback item.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 40 | BE-091 | n8n adapter for `DumpParser` over the HMAC httpx client, plus the exported schema in `integrations/n8n/` | BE-038, BE-041, BE-090, BE-110, BE-113 | Adapter | — | 80 | `make n8n-schemas` shows no diff; `MockTransport` tests pass |
| 41 | BE-112 | Build and export the `parse_dump` workflow: HMAC check node, LLM prompt (Spanish + English, dates in America/Mexico_City), strict JSON output; end-to-end check against the API (mostly human steps) | BE-041, BE-091, BE-111 | Pipeline | — | workflow JSON + 40 | M8 demo; a request with a bad signature is rejected inside n8n |

## M9: What now? through the API

**Demo:** with a few tasks of different sizes and dates: `POST /now {"energy":"low","availableMinutes":15}` → one task that fits, a *why* like "Due tomorrow, fits your 15 min, low energy is OK", and two alternates. Record `rerolled` → the next call ranks that task lower. `not-today` → the task is snoozed until tomorrow.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 42 | BE-101 | What now: request schema plus the candidates predicate (pure) | BE-081 | Specification | — | 90 | REPL: an L task isn't a candidate for 15 minutes |
| 43 | BE-102 | Scoring: urgency, fit, age, momentum, skip penalty → ranked list with factors (pure) | BE-101 | Pipeline | — | 140 | REPL: print the factors for three sample tasks; the due-tomorrow one wins |
| 44 | BE-103 | Fixed *why* line built from the factors (pure template) | BE-102 | Plain function | — | 60 | REPL: the sample's *why* reads naturally; no "overdue!!!" |
| 45 | BE-104 | `suggestions` table, migration and repository (record, recent skips) | BE-082 | Repository | — | 110 | `make api-migrate`; named repository tests |
| 46 | BE-105 | `POST /now` → `{task, why, alternates[], suggestionId}` | BE-085, BE-093, BE-103, BE-104 | Pipeline | — | 110 | `/docs` call from the demo; no candidates → `200` with `task: null` |
| 47 | BE-106 | `POST /now/{suggestionId}/action` (started, rerolled, not-today → snooze until tomorrow) | BE-088, BE-105 | Thin controller | — | 90 | M9 demo |

## M10: What now? in the browser

**Demo:** press `n` anywhere → two chip questions, prefilled with last time's answers (Skip works) → one big card: title, first step, *why*, Start · Another · Not today. Three Anothers → a gentle break suggestion. With no candidates → the kind 2-minute reset instead of an empty state.

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 48 | FE-045 | What now types plus API client | BE-106, FE-032 | Facade | — | 80 | Named client tests; `askNow()` in the console returns a task |
| 49 | FE-046 | Energy and time questions (skippable, remember the last answer) | FE-045, FE-040 | Custom hook | — | 120 | Fixture route: pick, reload, see the answer remembered; keyboard-only |
| 50 | FE-047 | What now card: title, first step, *why*, three buttons, kind "nothing fits" reset | FE-045, FE-040 | Presentational | — | 140 | Fixture route: card, reset state, phone width, reduced motion |
| 51 | FE-048 | Wire What now: `#now`, `n` shortcut, at most 3 rerolls then suggest a break | FE-035, FE-040, FE-046, FE-047 | Connected component | — | 120 | M10 demo |

## M11: Focus timer

**Demo:** from What now?, Start with 10 minutes → countdown with the task and first step visible → Done → the task is `done` in `#tasks` and a focus session with outcome `done` is in the DB. Stuck → a calm "break it down" note (the AI breakdown comes later).

| # | ID | Title | Depends on | Pattern | New package | Est. lines | Human check |
|---|---|---|---|---|---|---|---|
| 52 | BE-107 | Focus session schemas, `focus_sessions` table and migration | BE-082 | Immutable value objects | — | 100 | `make api-migrate`; REPL: outcome `"maybe"` is rejected |
| 53 | BE-108 | `POST /focus-sessions` and `PATCH /focus-sessions/{id}` (`done` completes the task) | BE-088, BE-107 | Thin controller | — | 120 | `/docs`: start, end with `done` → `GET /tasks/{id}` is `done` |
| 54 | FE-049 | Focus timer: pure `remaining()`, countdown, reduced motion, Done · More time · Stuck, fixture data | FE-031, FE-040 | Presentational | — | 150 | Fixture route with a 1-minute timer: it reaches 0 and shows the three buttons |
| 55 | FE-050 | Wire the focus timer to focus sessions (Start → session, Done → complete) | BE-108, FE-048, FE-049 | Connected component | — | 110 | M11 demo |

## Parallel work

- M1 is independent and can run any time.
- After BE-080, the tasks API (M2), the inbox API (M4) and the What now engine (BE-101–103) can be built side by side.
- FE-035, FE-036, FE-040, FE-049 and the fixture-only presentational tickets can start before their APIs exist.

## Decisions

- **Open questions:** the recommended answers are accepted.
  1. Contexts: home · computer · phone · errand · anywhere.
  2. What now? asks for energy and time, prefilled with the last answer, and both can be skipped.
  3. Focus lengths 10/25/45 min; the Telegram check-in is off by default.
  4. Morning top-3 message: deferred.
  5. Quiet hours 22:00–08:00, through the EPIC-010 notification policy.
  6. Raw voice notes and photos are discarded after parsing (reuse the BE-045 prompt).
  7. Parsing and bot replies in Spanish and English.
  8. No Google Calendar (non-goal).
- **Human-verifiable chunks:** work is grouped into 11 milestones, each with a demo, and every ticket has a human check (see "How this is chunked").
- **Parsing runs in n8n** (`parse_dump`), consistent with EPIC-008 architecture B. The API sends `today` in America/Mexico_City and validates n8n's output against a strict schema.
- **A dev splitter (BE-113)** makes multi-item dumps and Accept all testable by hand before n8n parsing (M8) is unblocked.
- **Presentational tickets** show their states on dev-only `#dev-<name>` screens from the FE-040 registry; each wiring ticket removes its dev screen. Component logic lives in pure helpers because the repo has no component-test library.
- **The inbox owns its parser port** (`DumpParser`, BE-090) instead of extending EPIC-008's `N8nClient`. The n8n adapter (BE-091) is one implementation, so M4–M7 run without n8n or BE-037, and a direct Claude adapter can replace n8n later without touching feature code.
- **Auth:** every route uses `require_principal`. Telegram input reaches the API through its own webhook, so n8n never calls these routes. Scoped keys (F-2) become later hardening.
- **The *why* line** is a fixed rule-based template; AI wording comes later.
- **n8n is self-hosted** from the official `n8nio/n8n` Docker image in the existing `docker-compose.yml`, behind an `n8n` profile so `make db-up` doesn't start it. Local only (`127.0.0.1:5678`); the API on the host reaches it at `N8N_BASE_URL=http://127.0.0.1:5678`, which BE-038 allows for dev. SQLite in a volume for dev; Postgres for n8n is a production-hosting decision. Production hosting is still undecided.
- **Licence:** n8n uses the Sustainable Use License (fair-code, not OSI open source). Self-hosting it for your own internal use is allowed; reselling it or offering it as a hosted service isn't.

## Blocked

- M8 only: BE-091 waits on BE-038 and BE-041; BE-112 waits on BE-041. Those EPIC-008 tickets aren't built yet.

Every other milestone is unblocked.

## Assumptions

- In Phase 1, Accept works for `task` and `reminder` items; a reminder becomes a task with a due date.
- `note` and `expense` items can only be snoozed or let go until the Notes entity and EPIC-002 exist.
- Presentational tickets show their states on a temporary fixture route (or a fixture toggle) that the wiring ticket removes.
- Any Docker image that runs the API needs `tzdata` installed so `zoneinfo` works.
- n8n's `/healthz` and `/healthz/readiness` endpoints, and `wget` inside the image for the healthcheck, are confirmed against the pinned image when BE-109 is built.
- The LLM provider key used inside n8n is a human step (stored as an n8n credential, never in the repo).

## Deferred (later phases)

The epic's status stays `draft` until these are ticketed or explicitly deferred.

- Telegram capture plus `/now`, `/inbox` and `/done`
- The Notes entity, and routing expenses to EPIC-002
- AI "Break it down" and recurrence
- Inbox nudges, the morning top-3 message and the halfway focus check-in
- The Settings screen
- AI-written *why* lines, and time-of-day learning
