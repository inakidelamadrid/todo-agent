# todo-agent API

FastAPI backend for todo-agent. **Every route requires an API key by default**;
only `GET /health` and `GET /ping` are public.

## Setup

Requires Python 3.12+ (managed automatically by `uv`).

```bash
cp .env.example .env   # then replace the placeholder with real keys
uv sync
```

### `API_KEYS`

Valid keys are configured via the `API_KEYS` environment variable (or `.env`),
as a **comma-separated list** so keys can be rotated:

```
API_KEYS=key-for-client-a,key-for-client-b
```

The app **refuses to start** when `API_KEYS` is missing or empty. Keys are
never logged or echoed. Clients send their key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: <key>" http://localhost:8000/some-protected-route
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Interactive docs (with an **Authorize** button for the API key) at
<http://localhost:8000/docs>.

## Test

```bash
uv run pytest -n auto
```

## Databases

Postgres 17 and Redis 7 run locally via Docker Compose (images pinned in
`docker-compose.yml`, ports bound to `127.0.0.1` only). The API app itself
does not connect to them yet — that is a separate ticket.

**Prerequisites:** Docker (or Docker Desktop) with Compose v2, and `make`.

### Credentials (one-time, manual)

```bash
cp .env.db.example .env.db   # at the repo root
```

Edit `.env.db` and replace **both** `change-me` passwords with your own.
`.env.db` is gitignored — never commit it. `make db-up` refuses to run while
the file is missing or still contains placeholder passwords.

### Make targets

Run from the repo root:

| Command | Description |
|---|---|
| `make help` | List all targets |
| `make db-up` | Start Postgres and Redis, wait until healthy |
| `make db-down` | Stop containers (data kept in named volumes) |
| `make db-restart` | Stop then start both databases |
| `make db-status` | Show containers and health |
| `make db-logs` | Follow logs; one service via `make db-logs s=postgres` or `s=redis` |
| `make db-psql` | Open a `psql` shell in Postgres |
| `make db-redis-cli` | Open an authenticated `redis-cli` |
| `make db-backup` | Dump Postgres to `backups/<timestamp>.sql` (gitignored) |
| `make db-reset` | **Destructive**: delete containers and volumes; asks for typed confirmation |

## Layout


```
app/
  main.py           # create_app() factory, mounts routers
  settings.py       # frozen pydantic-settings model, loaded once
  security.py       # require_api_key dependency (X-API-Key header)
  routes/
    public.py       # /health, /ping — the only unauthenticated routes
tests/
  test_public.py    # public endpoint tests
  test_auth.py      # auth behavior, incl. a test-only protected route
```

Repo root also holds `docker-compose.yml`, `Makefile` and `.env.db.example`
for the databases (see *Databases* above).

New routers are mounted with `dependencies=[Depends(require_api_key)]` in
`app/main.py`. A route becomes public only when a ticket says so explicitly.
