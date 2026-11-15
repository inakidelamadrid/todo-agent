---
name: unfold-epic
description: Break an epic from Epics/ into small, review-sized BE-/FE- tickets under tickets/. Use this whenever the user asks to unfold, break down, split, slice, plan or "ticket" an epic or a foundation (F-1…F-8), asks what tickets an epic needs, says an epic is ready, or asks for tickets to be made smaller or more detailed, even if they don't say "unfold".
---

# Unfold an epic into tickets

Turn one epic in `Epics/` into a sequence of tickets in `tickets/backend/` and `tickets/frontend/`, each small enough that Ignacio can read the whole diff, understand every line, and verify it himself.

**Why the tickets are this small.** Agents will write most of this code. The tickets are how the human stays the owner of it: if a ticket produces a diff too large to hold in your head, the review becomes a rubber stamp and the codebase drifts out of his understanding. Optimise for *his comprehension per ticket*, not for the fewest tickets or the fastest delivery. Twenty tiny tickets beat five big ones.

This skill only writes Markdown (tickets, the epic's breakdown section, the epics index). It never writes application code, installs packages, commits or pushes.

## Workflow

### 1. Read before slicing

Read all of these; the tickets must match what is really there, not what you assume.

- The epic, in full, plus `Epics/README.md` (lifecycle, shared foundations F-1…F-8, suggested order).
- `CLAUDE.md` (stack, functional style, domain model, secure-first, premium design) and `DESIGN.md` for anything user-facing.
- `tickets/README.md`, both workspace READMEs and both `_template.md` files.
- Existing tickets, to find the next free `BE-`/`FE-` numbers and to see what is already built or in flight.
- The code the epic touches or should imitate. `api/app/bills/` and `web/src/features/bills/` are the reference implementation of the house patterns.
- `web/package.json` and `api/pyproject.toml`, so you know what is already installed.

### 2. Check the epic is ready

- **Open questions.** Epics end with an "Open questions" section with `Answer:` lines. List every unanswered question that would change the tickets (scope, data shape, security, a library choice) and ask the user to answer them, with your recommended answer for each. Do not invent answers silently. If the user says to proceed anyway, write each assumption into the affected ticket under "Assumptions" and into the epic next to the question, marked `(assumed)`.
- **Dependencies.** For each foundation or epic under "Depends on", check whether tickets or code exist. If not, say so and offer either to unfold the dependency first or to mark the dependent tickets `blocked` with the reason. Slices that need no missing dependency should still be ticketed so work can start.

### 3. Slice

Work in thin vertical order so every ticket leaves `main` green and adds something that can be seen or tested on its own. A typical feature slices like this, one ticket per line; split further whenever a line holds more than one idea:

**Backend**
1. Pydantic schemas + validation tests (no DB, no routes).
2. Pure domain functions + tests (the rules, as plain functions).
3. SQLAlchemy model + Alembic migration.
4. Repository functions, one or two operations per ticket.
5. One route (or one tightly related pair, e.g. `GET` list + `GET` by id) per ticket, including its auth test.
6. Each background job, each external integration, each adapter: its own ticket. Put the port (the function signature the rest of the app calls) and a fake in one ticket, the real integration in the next.

**Frontend**
1. Types + pure model functions + tests.
2. API client functions for one resource + tests.
3. Store slice / state transitions + tests.
4. One presentational component per ticket, with all its states (loading, empty, error, hover, focus), fed by fixture data.
5. Wiring: connect the component to the store and API.
6. Each interaction that has its own failure mode (optimistic update, form submit, undo) on its own.

**Size limits.** These are what "reviewable" means here; treat going over as a signal to split, and say why in the ticket if a split is truly impossible.

| Limit | Target |
|---|---|
| Concepts introduced | 1 |
| Files created or changed (excluding tests, lockfiles, generated migrations) | ≤ 5 |
| Non-test lines changed | ≤ ~150 |
| Time for a human to review | ≤ 15 minutes |
| New dependencies | ≤ 1, and installing it is its own acceptance criterion |
| Acceptance criteria | 3–7, each checkable by a command or by looking |

Other slicing rules:

- A ticket belongs to one workspace. Cross-side features become a `BE-` ticket and an `FE-` ticket linked by `Depends on`.
- Refactors that make room for a feature are their own ticket, before the feature, with no behaviour change.
- Never mix "add a dependency / config / migration" with "use it in three places".
- Order tickets so each depends only on earlier ones. Mark tickets that can run in parallel.
- If a concept will be new to the reader (e.g. idempotency keys, webhook signature verification, optimistic rollback), introduce it in the smallest possible ticket first, so later tickets build on something already understood.

### 4. Choose patterns and packages

For each ticket, name the design pattern it applies and the package it leans on, and say why in one or two sentences. This is part of keeping the human in the loop: the ticket teaches the shape of the solution before the code exists.

- Patterns: read `references/patterns.md`. Prefer the functional form of each pattern and the way `bills` already does it. Do not add a pattern the ticket doesn't need; "plain function, no pattern" is a valid answer.
- Packages: read `references/packages.md`. Reuse what is installed first, then a well-established package, and hand-write only small, domain-specific logic. Verify any new package against its registry before recommending it; never recommend from memory alone.

### 5. Show the outline and wait

Before writing any file, show the breakdown as one table and stop for approval:

| # | ID | Title | Depends on | Pattern | New package | Est. lines |
|---|---|---|---|---|---|---|

Follow it with: unanswered questions and assumptions, blocked tickets and why, and anything you deliberately left out of scope. The user will often merge, split or reorder here; that is the point of the pause.

### 6. Write the tickets

After approval:

- Create one file per ticket using `references/ticket-template.md`, named like the existing ones (`BE-004-short-title.md`), continuing each folder's numbering. The template is a superset of the folders' `_template.md` files; keep their header fields exactly so existing agents can still read them.
- Replace the epic's "Proposed ticket breakdown (draft)" section with the real ordered list, linking each ticket, and showing dependencies. This is the epic's map; do not create a separate planning document.
- Set the epic's `Status` to `in-tickets` in the epic and in the `Epics/README.md` table (only if every part of the epic is ticketed or explicitly deferred; otherwise leave the status and note what remains).
- Report the files written. Do not commit.

## What makes a ticket good here

A ticket is done being written when someone who has not read the epic could implement it, and Ignacio could review the result against it without opening anything else.

- **Exact, not vague.** Name file paths, function names with signatures, field names with types and limits, endpoint method + path + status codes, example JSON. "Add validation" is not a requirement; "`title`: 1–120 chars, trimmed; empty → `422`" is.
- **Explains the why.** One short paragraph on where this ticket sits in the epic and why it is shaped this way.
- **Says what to read first.** Point at the existing file that the new code should look like.
- **Tests are listed by name and intent**, not "add tests". Every protected route gets a missing-key and wrong-key test.
- **A review guide** tells the human what to look at in the diff, in order, and what questions the code should answer.
- **A verify section** gives the exact commands or clicks a human runs to see it work.
- **Out of scope** names the tempting next step and the ticket that owns it.

## Project rules every ticket must respect

These come from `CLAUDE.md`; bake them into the ticket's details and acceptance criteria rather than restating them generically.

- Every endpoint needs an API key through the shared dependency unless the epic explicitly makes it public; a public endpoint must say how it is guarded (token, signature, allowlist).
- Money is integer cents with a per-record currency. JSON is camelCase; Python is snake_case with `to_camel` aliases. Months `YYYY-MM`, dates `YYYY-MM-DD`.
- Functional style: pure functions in the core, side effects at the edges, immutable data, no classes beyond data models and error types.
- A shared model changes on both sides together: pair the `BE-` and `FE-` tickets and link them.
- User-facing tickets must name the states to polish and reference the tokens and idioms in `DESIGN.md`.
- Secrets come from environment variables; a ticket that needs a new one adds it to the `.env.example` file and includes a human step to set the real value.
