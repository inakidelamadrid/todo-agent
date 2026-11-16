# todo-agent — Project Rules

## Stack

- **Backend:** Python + FastAPI.
- **Frontend:** React (TypeScript) + shadcn/ui for components, styled with Tailwind CSS. Built and bundled with **Vite**.
- **Backend tests:** pytest, run in parallel with pytest-xdist (`pytest -n auto`) for speed. Use FastAPI's `TestClient` for endpoint tests, and cover the API-key protection on every protected route.

## Code style: functional programming

Applies to the whole codebase: frontend controllers, models, and backend.

- Prefer pure functions; keep side effects (I/O, DB, network, state) at the edges.
- Favor immutability: no mutating inputs or shared state; return new values.
- Compose small, single-purpose functions instead of classes and inheritance.
- Frontend: function components and hooks only; no class components.
- Backend: plain functions for routes, services, and logic; use immutable data models (e.g. frozen Pydantic models / dataclasses).

## Domain model: bills & payments

One model, shared by frontend and backend. Change both sides together.

- **Sources of truth:**
  - Frontend: `web/src/features/bills/model/types.ts`, with logic in `schedule.ts`.
  - Backend: `api/app/bills/` (`schemas.py`, `models.py`, `domain.py`).
- **JSON on the wire is camelCase.** Python stays snake_case and uses Pydantic `alias_generator=to_camel`.
- **Money is always integer cents** (`estimatedCents`, `actualCents`, 0–1 000 000 000). Never use floats. Each bill has its own currency (`MXN` | `USD`), and totals are per currency, never converted.
- **Months are `YYYY-MM` strings and dates are `YYYY-MM-DD`.**

**Bill**

| Field | Type / rules |
|---|---|
| `id` | UUID, server-generated |
| `name` | 1–80 characters, trimmed |
| `note` | 0–200 characters, default `""` |
| `line` | `utilities` \| `telecom` \| `streaming` \| `software` (the category; each is one "line" on the network map) |
| `currency` | `MXN` \| `USD` |
| `estimatedCents` | int; the expected amount |
| `dueDay` | 1–31; clamped to the month's last day when displayed |
| `recurrence` | `monthly` \| `bimonthly` \| `yearly` |
| `startMonth` | `YYYY-MM`; the first month it's due |
| `createdAt` / `updatedAt` | server-managed, UTC |

**Payment**: at most one per bill per period. The primary key is `(billId, period)`, and deleting a bill deletes its payments.

| Field | Type / rules |
|---|---|
| `billId` | UUID → Bill |
| `period` | `YYYY-MM`; the bill must be due that month |
| `actualCents` | int; what was actually paid. It replaces the estimate in totals |
| `paidAt` | `YYYY-MM-DD` |

**Rules**
- **Due rule:** a bill is due in month `m` when `m >= startMonth` and `(m − startMonth)` in months is divisible by 1 / 2 / 12. This is `isDueInMonth` in the frontend and `is_due_in_month` in the backend.
- **Status** (frontend only): `paid` if a payment exists; otherwise `overdue` (past its due date), `due-soon` (due within 3 days), or `upcoming`.
- **API**, protected by `X-API-Key`:
  - `GET`/`POST /bills`
  - `GET`/`PATCH`/`DELETE /bills/{id}`
  - `PUT`/`DELETE /bills/{id}/payments/{period}`: mark paid as an idempotent upsert, and undo
  - `GET /payments?month=YYYY-MM`

## Backend: secure first

- Security comes first in every backend decision.
- **Every endpoint requires an API key by default.** An endpoint is public only when I explicitly say to make it public.
- Enforce the API key via a shared FastAPI dependency, not ad-hoc checks per route.
- Never hardcode keys; load them from environment variables.

## Design: premium everywhere

- Everything user-facing must look **premium**: refined, polished, intentional — never default or templated.
- Typography: a deliberate type scale, generous line-height, a quality font pairing (no browser defaults).
- Spacing: generous whitespace, consistent spacing scale, clear visual hierarchy.
- Color: restrained palette with one accent; define colors as tokens; support light and dark mode.
- Details: subtle shadows, soft radii, smooth transitions and micro-interactions, crisp icons.
- Polish every state: hover, focus, active, loading, empty, error.
- Responsive and accessible: works at phone width, good contrast, keyboard-friendly.

## Communication

- Keep responses **shorter than usual**: lead with the result, skip filler and long recaps.

## Ticket work: start ritual

When the user says **"Start working on feature/ticket XYZ"** (any ticket id):

1. Switch to `main` and pull latest.
2. Read the ticket's `Depends on:` list. If any dependency's PR is not yet merged into `main`, **stop and report** which ones are missing — do not start.
3. Otherwise create branch `idelamadrid/<ticket-id>` and start the work.

## Never send without asking

- **Never send, post, publish, share, email, message, push, or deploy anything without asking first** and getting an explicit yes.
- This includes git pushes, PRs, artifacts, messages, and any upload to an external service.
- Approval covers only that one action; ask again for the next.
