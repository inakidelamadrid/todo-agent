# BE-003: Bills models, persistence and protected router

- **Status:** todo
- **Workspace:** backend
- **Assigned agent / harness / model:**
- **Depends on:** BE-001 (FastAPI + API key auth), BE-002 (Postgres + Redis via Docker / `make`)
- **Public endpoint?** no. Every route here requires `X-API-Key`.

## Goal

Persist bills and their monthly payments in Postgres, and expose a protected `/bills` router. The frontend bills view (currently Zustand + localStorage) can then switch to the API in a later FE ticket without changing its data model.

**Out of scope:**
- Computing month views or totals on the server (the frontend does this).
- Users, multi-tenancy, authorization.
- Using Redis.
- Frontend integration.
- Seeding sample data.

## Starting point (state after BE-002)

Pull `main` first and branch from it.

- `api/` is FastAPI with `create_app()`, a frozen `Settings` (pydantic-settings, `env_file=".env"`), and `require_api_key` in `app/security.py`. Only `routes/public.py` exists (`/health`, `/ping`). New routers must be mounted with `dependencies=[Depends(require_api_key)]`.
- Postgres 17 runs through `docker-compose.yml` at the repo root. Its credentials are in **`.env.db`** at the repo root (gitignored): `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`. Postgres listens on `127.0.0.1` only.
- The `make db-*` targets exist (`db-up`, `db-status`, `db-psql`, …).
- The API is **not connected to Postgres yet**: there is no driver, ORM or migrations.
- Tests: 14 passing with `uv run pytest -n auto` from `api/`. `conftest.py` sets a fallback `API_KEYS` before importing the app.

## Domain model (must match the frontend)

Mirror `web/src/features/bills/model/types.ts`. JSON uses **camelCase**: Python stays snake_case, and Pydantic models use `alias_generator=to_camel`, `populate_by_name=True`.

**Bill**

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Server-generated |
| `name` | string | 1–80 characters after trimming |
| `note` | string | 0–200 characters, default `""` |
| `line` | enum | `utilities` \| `telecom` \| `streaming` \| `software` |
| `currency` | enum | `MXN` \| `USD` |
| `estimatedCents` | int | 0 to 1 000 000 000. Money is always integer cents, never float |
| `dueDay` | int | 1–31. The client clamps it to the month's length |
| `recurrence` | enum | `monthly` \| `bimonthly` \| `yearly` |
| `startMonth` | string | `YYYY-MM`, a valid month |
| `createdAt` / `updatedAt` | datetime | Server-managed, UTC |

**Payment**: at most one per bill per period.

| Field | Type | Rules |
|---|---|---|
| `billId` | UUID | FK to the bill, `ON DELETE CASCADE` |
| `period` | string | `YYYY-MM`, and the bill must be **due** that month (see below) |
| `actualCents` | int | 0 to 1 000 000 000 |
| `paidAt` | date | `YYYY-MM-DD` |

Put a unique constraint on `(bill_id, period)`.

**Due rule.** Port it as a pure function with unit tests. A bill is due in month `m` when `m >= startMonth` and the month difference is divisible by 1 (monthly), 2 (bimonthly) or 12 (yearly). This matches `isDueInMonth` in `web/src/features/bills/model/schedule.ts`.

## Persistence

- Add the dependencies **SQLAlchemy 2 (async)**, **asyncpg** and **Alembic**. Use `uv add`, then commit the updated `uv.lock`.
- **Settings:**
  - Read the database values from the repo-root `.env.db` as a second env file (for example `env_file=(".env", "../.env.db")`), so there is one source of truth for credentials.
  - Add `postgres_host` (default `127.0.0.1`).
  - Keep `postgres_password` as a `SecretStr`.
  - Expose a derived, read-only `database_url` (`postgresql+asyncpg://…`).
  - Never log or print the DSN.
- **Engine and session:** create the engine once in an app lifespan and dispose it on shutdown. Provide a `get_session` dependency (`AsyncSession`) with one transaction per request.
- **Migrations:** run Alembic in `api/migrations/`. The first revision creates `bills` and `payments`. Postgres enums or `CHECK` constraints must enforce the same rules as the API, and there's an index on `payments.period`.
- **Code layout:** keep the core functional and layered. The ORM models and Pydantic schemas are the only classes.

  ```
  app/bills/
    domain.py        # pure: is_due_in_month, month parsing/validation
    schemas.py       # frozen Pydantic: BillCreate, BillUpdate, BillOut, PaymentIn, PaymentOut
    models.py        # SQLAlchemy ORM tables
    repository.py    # async functions taking a session; no HTTP concerns
    router.py        # thin: validate → repository → schema
  app/db.py          # engine, session factory, get_session
  ```

## Endpoints

All of these are mounted under `dependencies=[Depends(require_api_key)]`.

| Method | Path | Behaviour |
|---|---|---|
| `GET` | `/bills` | List bills. Optional `?line=` filter. Order by `dueDay`, then `name` |
| `POST` | `/bills` | Create → `201` + `BillOut` + `Location` header |
| `GET` | `/bills/{id}` | `BillOut` or `404` |
| `PATCH` | `/bills/{id}` | Partial update (all fields optional, same validation) → `BillOut` |
| `DELETE` | `/bills/{id}` | `204`. Cascades its payments |
| `GET` | `/payments?month=YYYY-MM` | Payments for that month (`month` is required) |
| `PUT` | `/bills/{id}/payments/{period}` | Mark paid: body `{actualCents, paidAt}`. Idempotent upsert → `200` + `PaymentOut`. Returns `422` if the bill is not due in `period` |
| `DELETE` | `/bills/{id}/payments/{period}` | Undo paid → `204`. Idempotent: `204` even if it was unpaid |

- **Errors:**
  - `404` → `{"detail": "Bill not found"}`.
  - Validation errors use FastAPI's standard `422` shape.
  - Never return a `500` for bad input.
- **OpenAPI:** each route has a summary, response models and the `bills` / `payments` tags. `/docs` must show the lock icon on every route.

## `make` targets

Add these to the root `Makefile`, listed by `make help`:

| Target | Does |
|---|---|
| `make api-migrate` | Run `alembic upgrade head` (requires `make db-up`) |
| `make api-revision m="message"` | Autogenerate a new Alembic revision |
| `make api-test` | Run `uv run pytest -n auto` in `api/` |
| `make api-dev` | Start uvicorn with reload on `127.0.0.1:8000` |

## Tests

These must stay parallel-safe with `pytest -n auto`.

- **Unit tests (no database):**
  - `is_due_in_month`: monthly, bimonthly and yearly; before `startMonth`; across year boundaries.
  - Month validation.
  - Schema validation edges: name blank or too long, `dueDay` 0 or 32, negative cents, bad `YYYY-MM`.
- **Integration tests (real Postgres from `make db-up`):**
  - Each xdist worker uses its **own test database** (for example `<POSTGRES_DB>_test_<worker_id>`). A fixture creates it, runs the migrations, and drops it at the end. Tests never touch the dev database.
  - If Postgres isn't reachable, fail with a clear message telling the human to run `make db-up`. Do not silently skip.
- **Cover:**
  - Full CRUD.
  - `PATCH` partial updates.
  - Cascade delete.
  - The payment upsert is idempotent and replaces the amount.
  - Paying in a not-due month → `422`.
  - Undo is idempotent.
  - `GET /payments` returns only the requested month.
  - **Every `/bills` and `/payments` route returns `401` without or with a wrong key.**
- BE-001's existing tests keep passing.

## Human-in-the-middle

No new credentials are needed: the API reuses `.env.db`. If `.env.db` is missing, stop and tell the human to create it, following BE-002 (`cp .env.db.example .env.db`, set both passwords), then wait.

## Acceptance criteria

- [ ] `make db-up && make api-migrate` creates `bills` and `payments` with constraints matching the API rules.
- [ ] All endpoints behave as in the table, with camelCase JSON matching the frontend types.
- [ ] Every new route requires a valid `X-API-Key` (`401` otherwise), with tests for each route.
- [ ] Money is stored and returned as integer cents only.
- [ ] `make api-test` passes in parallel on isolated per-worker test databases, and the dev data is untouched.
- [ ] No DSN, password or API key appears in logs, responses, committed files or this ticket.
- [ ] `api/README.md` documents migrations, the new `make` targets and an example `curl` call with `-H "X-API-Key: …"`.
- [ ] Code follows `CLAUDE.md`: functional core, frozen schemas, secure first.
- [ ] **Final handoff:** list the new `make` commands and the endpoint table for the human.
- [ ] Nothing is committed or pushed without asking the user first.

## Notes / log

The agent adds progress notes, decisions and open questions here. Never log credentials.
