# Ticket template

Use this for both workspaces. The header block and the Goal / Details / Acceptance criteria / Notes sections match `tickets/backend/_template.md` and `tickets/frontend/_template.md`; the other sections are additions. Delete a section only when it truly has nothing to say (e.g. "Packages" → "None new").

```markdown
# BE-000: Title that names the one thing this adds

- **Status:** todo
- **Workspace:** backend | frontend
- **Epic:** [EPIC-00N: Name](../../Epics/EPIC-00N-name.md) §5.1
- **Assigned agent / harness / model:**
- **Depends on:** BE-000, FE-000 (or none)
- **Can run in parallel with:** BE-000 (or none)
- **Public endpoint?** no (backend only; if yes, say how it is guarded)
- **Review size:** ~120 lines, 4 files, ~10 min

## Goal

What is true when this is done, in one or two sentences. One idea only.

## Why this ticket exists

Where it sits in the epic, what the previous ticket left and what the next one needs. Why it is cut here.

## Read first

- `api/app/bills/repository.py`: the shape to imitate (functions take a session, do one thing).
- Any concept that may be new, in two or three plain sentences, with a link to the official docs.

## Design

- **Pattern:** name + one or two sentences on why it fits and how it shows up in the code (see the skill's `references/patterns.md`).
- **Data flow:** request → validation → pure function → repository → response (or component → store action → client → API), naming the functions involved.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `pydantic` | installed | request validation | already the house standard |
| `some-package` | **new** | … | version, licence, last release, weekly downloads; alternatives considered |

Hand-written instead of a package: what and why (only when relevant).

## Details

Exact and complete. As applicable:

- **Files:** each path, marked new or changed, with what goes in it.
- **Functions:** name, signature, behaviour, edge cases. Mark which are pure.
- **Data:** fields with type, limits, defaults; migration name; indexes.
- **API:** method + path, request and response JSON examples (camelCase), every status code and when it happens.
- **UI:** component name, props, every state (loading, empty, error, hover, focus, disabled), tokens from `DESIGN.md`, behaviour at phone width, keyboard behaviour.
- **Config:** new env vars, added to the `.env.example` file.

## Steps

1. Small, ordered implementation steps, each ending in something runnable.
2. …

## Tests

- `test_name_states_the_behaviour`: what it proves.
- Backend routes: missing API key → `401`; wrong key → `401`.

## Acceptance criteria

- [ ] Observable behaviour, checkable by a command or by looking
- [ ] …
- [ ] Endpoints reject requests without a valid API key (backend, unless marked public)
- [ ] Tests pass (`pytest -n auto` | `npm --prefix web test`) and, for frontend, the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths (frontend, when visible)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Exact commands or clicks, with the expected result.

## Review guide

Read the diff in this order, and check:

1. `path/file`: the one question this file should answer.
2. …

Things that should *not* be in the diff: …

## Out of scope

- The tempting next step → owned by BE-000.

## Assumptions

Only if an open question was unanswered: the assumption, and what changes if it is wrong.

## Notes / log

The agent adds progress notes, decisions and open questions here.
```
