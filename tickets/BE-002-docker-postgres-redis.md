# BE-002: Docker setup for Postgres and Redis, managed with `make`

- **Status:** todo
- **Workspace:** backend
- **Assigned agent / harness / model:**
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

- [ ] The agent stopped before setup, told the human exactly where and how to add credentials (`.env.db` at the repo root), and waited for confirmation.
- [ ] `make db-up` fails with a helpful message when `.env.db` is missing or still has `change-me` passwords.
- [ ] After the human fills in `.env.db`, `make db-up` starts Postgres and Redis and both report **healthy** in `make db-status`.
- [ ] `make db-psql` connects. `make db-redis-cli` connects, and `PING` returns `PONG` only with the password.
- [ ] Data survives `make db-down` + `make db-up`. `make db-reset` asks for confirmation and then wipes it.
- [ ] Ports listen on `127.0.0.1` only. Images are pinned to exact versions.
- [ ] No credential appears in any committed file, in command output or in the ticket log. `.env.db` and `backups/` are gitignored.
- [ ] BE-001's tests still pass: `pytest -n auto` from `api/`.
- [ ] **Final handoff:** the agent ends by giving the human the list of `make` commands, with a one-line description of each, ready to copy.
- [ ] Nothing is committed or pushed without asking the user first.

## Notes / log

The agent adds progress notes, decisions and open questions here. Never log credentials.
