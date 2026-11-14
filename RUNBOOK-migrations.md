# Database Migrations Runbook

How to evolve the Postgres schema safely in local development. Migrations are
managed with **Alembic** in `api/migrations/`, driven by root `make` targets.

## Prerequisites

- Databases running: `make db-status` shows Postgres `healthy`. If not: `make db-up`.
- `api/` dependencies synced (`uv sync`, done once after clone/pull).

## Concepts

- **One source of truth for credentials:** `../.env.db` (repo root, gitignored).
  The app and Alembic both read it via `api/app/settings.py`.
- **No DSN is ever committed.** `api/alembic.ini` has no `sqlalchemy.url`;
  `migrations/env.py` builds it at runtime from Settings. Never paste a DSN
  or password into migrations, the ticket log, or chat.
- **Test databases are isolated.** `make api-test` creates, migrates and drops
  `<dev-db>_test_<worker>` per pytest-xdist worker. The dev database is never
  touched by tests.

## Everyday workflow

1. **Change the model.** Edit `api/app/bills/models.py` (or add a new module's
   `models.py` and import it in `api/migrations/env.py` so `Base.metadata`
   sees the tables).
2. **Generate the revision:**

   ```bash
   make api-revision m="short description of the change"
   ```

3. **Review the generated file** in `api/migrations/versions/`. Autogenerate
   is a draft: check types, constraints, indexes, defaults and that the
   `downgrade()` is correct. Edit by hand when needed.
4. **Apply it:**

   ```bash
   make api-migrate
   ```

5. **Run the tests:** `make api-test`.

## Common operations

| Task | Command |
|---|---|
| Apply all pending migrations | `make api-migrate` |
| New revision (autogenerate) | `make api-revision m="message"` |
| Current revision of the dev DB | `cd api && uv run alembic current` |
| History | `cd api && uv run alembic history` |
| Roll back one step | `cd api && uv run alembic downgrade -1` |
| Roll back everything | `cd api && uv run alembic downgrade base` |

Rollback is safe only while data is disposable. Prefer forward-only fixes
(a new revision) once real data exists.

## Rules

- **Every schema change goes through a migration.** No manual `psql` edits to
  the dev schema — they drift from Alembic's view and break autogenerate.
- **DB constraints mirror API validation** (CHECK constraints in the models).
  The database must reject what the API rejects.
- **Small, reversible revisions.** One logical change per revision; always
  implement `downgrade()`.
- **Never commit secrets.** Revisions contain DDL only — no DSNs, passwords
  or API keys.

## Troubleshooting

- **`make api-migrate` says Postgres is not running** → `make db-up`, retry.
- **Password authentication failed** → `.env.db` was edited after the
  containers were created, or a password contains `$` (docker-compose
  collapses `$$`→`$`, mismatching what Python reads). Change the password to
  avoid `$`, then `make db-reset` (wipes data!) + `make db-up` because the
  password is baked into the volume on first init.
- **Autogenerate detects spurious changes** → the dev DB schema drifted from
  migrations (manual edits, or a partially-applied revision). Run
  `cd api && uv run alembic stamp head` only if you are certain the schema
  matches; otherwise inspect with `make db-psql` and reconcile by hand.
- **A migration failed halfway** → Postgres wraps DDL in transactions, so a
  failed revision leaves no partial state. Fix the revision file and re-run
  `make api-migrate`.
- **Reset everything** (dev only, destructive): `make db-reset`, then
  `make db-up && make api-migrate`.
