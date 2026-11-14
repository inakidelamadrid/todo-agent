# BE-002: Docker setup for Postgres and Redis, managed with `make`

- **Status:** done (implemented and verified on branch `idelamadrid/BE-002-docker-postgres-redis`; not committed — awaiting user approval)
- **Workspace:** backend
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** BE-001 (FastAPI scaffold in `api/`)
- **Public endpoint?** no new endpoints

## Goal

Run the backend's databases, **Postgres** and **Redis**, locally with Docker Compose. Credentials come only from an env file the human fills in, and simple `make` commands start, stop and inspect the databases.

**Out of scope:**
- Connecting the FastAPI app to the databases (ORM, migrations, Redis client, `DATABASE_URL` wiring).
- Dockerizing the FastAPI app itself.
- Production deployment.

Each of these becomes its own ticket.

## Details

### Files to create

```
docker-compose.yml        # repo root: postgres + redis services
Makefile                  # repo root: db-* targets
.env.db.example           # placeholders only, committed
.env.db                   # real credentials, filled in by the human, gitignored
```

Add `.env.db` to the root `.gitignore`.

### Credentials (human-in-the-middle step)

`.env.db.example` lists every variable with **placeholder** values:

```
POSTGRES_USER=todo_agent
POSTGRES_PASSWORD=change-me
POSTGRES_DB=todo_agent
POSTGRES_PORT=5432
REDIS_PASSWORD=change-me
REDIS_PORT=6379
```

- Never write real passwords anywhere: not in files, commits, logs or chat.
- Don't generate the credentials yourself; the human chooses them.
- **Before running any setup** (`make db-up`, pulling images, creating volumes), the agent must **stop and tell the human**:
  1. the exact file to create: `cp .env.db.example .env.db`, at the repo root.
  2. which variables to fill in, and that both passwords must be changed from `change-me`.
  3. that `.env.db` is gitignored and must never be committed.

  Then **wait for the human to confirm** before continuing.
- `make db-up` must refuse to run, with a clear message pointing to `.env.db`, if `.env.db` is missing or either password is still `change-me`.

### `docker-compose.yml`

- Use **pinned** image versions, never `latest`: e.g. `postgres:17.x-alpine` and `redis:7.x-alpine`, set to exact current versions.
- Read all credentials from `.env.db` (`env_file` / variable substitution), with nothing hardcoded.
- Bind ports to **localhost only**: `127.0.0.1:${POSTGRES_PORT}:5432` and `127.0.0.1:${REDIS_PORT}:6379`.
- Redis runs with a password (`--requirepass ${REDIS_PASSWORD}`) and AOF persistence (`--appendonly yes`).
- Each service gets a **named volume** for data (`postgres_data`, `redis_data`).
- Healthchecks: `pg_isready` for Postgres and an authenticated `redis-cli ping` for Redis.
- Set `restart: unless-stopped` and use a compose project name of `todo-agent`.

### `Makefile`

`make help` is the default target and lists every target with a one-line description. All targets pass `--env-file .env.db`.

| Target | Does |
|---|---|
| `make help` | List targets |
| `make db-up` | Check `.env.db`, start both services detached, wait until healthy |
| `make db-down` | Stop and remove the containers; **data is kept** |
| `make db-restart` | Run `db-down` then `db-up` |
| `make db-status` | Show containers and health |
| `make db-logs` | Follow logs for both, or one with `s=postgres` / `s=redis` |
| `make db-psql` | Open a `psql` shell in the Postgres container |
| `make db-redis-cli` | Open an authenticated `redis-cli` in the Redis container |
| `make db-backup` | Dump Postgres to `backups/<timestamp>.sql`; gitignore `backups/` |
| `make db-reset` | **Destructive:** remove containers **and volumes**. Must ask for typed confirmation (`Type 'reset' to delete all database data:`) |

Passwords must not show up in `make` output; mark the recipes silent with `@` where needed.

### Documentation

Add a "Databases" section to `api/README.md` covering:
- prerequisites (Docker / Docker Desktop)
- the credentials step
- the `make` targets.

## Acceptance criteria

- [x] The agent stopped before setup, told the human exactly where and how to add credentials (`.env.db` at the repo root), and waited for confirmation.
- [x] `make db-up` fails with a helpful message when `.env.db` is missing or still has `change-me` passwords.
- [x] After the human fills in `.env.db`, `make db-up` starts Postgres and Redis and both report **healthy** in `make db-status`.
- [x] `make db-psql` connects. `make db-redis-cli` connects, and `PING` returns `PONG` only with the password.
- [x] Data survives `make db-down` + `make db-up`. `make db-reset` asks for confirmation and then wipes it.
- [x] Ports listen on `127.0.0.1` only. Images are pinned to exact versions.
- [x] No credential appears in any committed file, in command output or in the ticket log. `.env.db` and `backups/` are gitignored.
- [x] BE-001's tests still pass: `pytest -n auto` from `api/`.
- [x] **Final handoff:** the agent ends by giving the human the list of `make` commands, with a one-line description of each, ready to copy.
- [x] Nothing is committed or pushed without asking the user first.

## Notes / log

The agent adds progress notes, decisions and open questions here. Never log credentials.

- Branch `idelamadrid/BE-002-docker-postgres-redis` from up-to-date `main`.
- Created `docker-compose.yml` (pinned `postgres:17.12-alpine3.24`, `redis:7.4.12-alpine3.22`; ports bound to `127.0.0.1`; named volumes `postgres_data`/`redis_data`; healthchecks via `pg_isready` and authenticated `redis-cli ping`; `restart: unless-stopped`; project name `todo-agent`).
- Decision: Redis `--requirepass` reads `$REDIS_PASSWORD` from container env at startup (`sh -c`), so the password never appears in `docker-compose.yml` or `docker compose config` output. Same for the Redis healthcheck (`REDISCLI_AUTH`).
- Created `Makefile` with all `db-*` targets; every target passes `--env-file .env.db`; passwords never printed (silent `@` recipes; auth via in-container env vars). `db-reset` requires typing `reset`.
- Guard `check-env` blocks `db-up` when: `.env.db` missing, either password still `change-me`, or empty. All three rejections verified (missing-file rejection in repo; placeholder rejections in a scratch dir — the agent never creates the repo's `.env.db`).
- `docker compose config` validates cleanly (scratch dir with placeholder env).
- `.env.db` and `backups/` added to root `.gitignore`. No credential written to any file, output, or this log.
- **Paused before any image pull / `db-up`** for the human credentials step, per ticket. Pending verification after confirmation: healthy start, psql/redis-cli connectivity, persistence, then BE-001 tests re-run.
- Human confirmed credentials (passwords never shared with the agent). Full verification completed:
  - `make db-up` → both containers pulled, started, **healthy** (compose `--wait`); `db-status` shows ports bound to `127.0.0.1` only.
  - `psql` connects; row written. Unauthenticated `redis-cli ping` → `NOAUTH`; authenticated → `PONG`.
  - Row + Redis key **survived** `db-down` + `db-up`.
  - `make db-backup` wrote `backups/<timestamp>.sql` (gitignored).
  - `make db-reset` **aborted** on wrong input, wiped containers+volumes on typed `reset`; test data confirmed gone; fresh `db-up` healthy again.
  - BE-001 suite: 14 passed via `pytest -n auto`.
- Docker Desktop was not running; agent started it (`open -a Docker`) before setup.
