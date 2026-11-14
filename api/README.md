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

New routers are mounted with `dependencies=[Depends(require_api_key)]` in
`app/main.py`. A route becomes public only when a ticket says so explicitly.
