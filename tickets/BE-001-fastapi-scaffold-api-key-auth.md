# BE-001: Scaffold the FastAPI app with API key authentication

- **Status:** done (implemented on branch `idelamadrid/BE-001-fastapi-scaffold`; not committed — awaiting user approval)
- **Workspace:** backend
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** none
- **Public endpoint?** yes, only `GET /health` and `GET /ping`. Everything else needs an API key.

## Goal

Start the backend: a FastAPI app in `api/` with API key **authentication** and two public endpoints, `GET /health` and `GET /ping`. Every route added later is protected by default.

**Out of scope:** authorization (roles, permissions, per-user access), users, a database, and any business endpoints.

## Details

### Project layout

- Create the app in `api/` at the repo root, next to `web/`.
- Python 3.12+, with dependencies managed in `api/pyproject.toml`. Use `uv` if it's installed, otherwise `pip` with a venv.
- Dependencies: `fastapi`, `uvicorn[standard]`, `pydantic-settings`.
- Dev dependencies: `pytest`, `pytest-xdist`, `httpx`.
- Suggested structure, kept functional with plain functions and no classes beyond Pydantic models:

  ```
  api/
    pyproject.toml
    .env.example          # API_KEYS=change-me
    app/
      main.py             # create_app() factory, mounts routers
      settings.py         # frozen pydantic-settings model, loaded once
      security.py         # API key dependency
      routes/
        public.py         # /health, /ping (no auth)
    tests/
      test_public.py
      test_auth.py
  ```

### Authentication (API key)

- The client sends its key in the `X-API-Key` header.
- Valid keys come from the `API_KEYS` env var, as a comma-separated list so keys can be rotated.
  - Never hardcode keys or commit a real one.
  - `.env.example` holds a placeholder only.
  - Add `.env` to `.gitignore`.
- One shared dependency, `require_api_key`, in `security.py`:
  - Compare keys with `secrets.compare_digest` (constant time).
  - On a missing or wrong key, return `401 Unauthorized` with body `{"detail": "Invalid or missing API key"}` and header `WWW-Authenticate: ApiKey`.
  - Never log or echo the key.
- **Protected by default.** Mount all non-public routers with `dependencies=[Depends(require_api_key)]`. Public routes live only in `routes/public.py`, and a route becomes public only when a ticket says so explicitly.
- If `API_KEYS` is empty or missing, the app must **fail at startup**. It must never run with auth turned off.
- Show the key in OpenAPI docs as an `APIKeyHeader` security scheme, so `/docs` has an "Authorize" button.

### Public endpoints (no API key)

| Method | Path | Response `200` |
|---|---|---|
| GET | `/health` | `{"status": "ok", "version": "<app version>"}` |
| GET | `/ping` | `{"ping": "pong"}` |

### Run

- Dev: `uv run uvicorn app.main:app --reload --port 8000`, run from `api/`.
- Add a short `api/README.md` covering how to set `API_KEYS`, run the app and run the tests.

## Acceptance criteria

- [x] `GET /health` and `GET /ping` return `200` with the bodies above, with no API key.
- [x] Any other route returns `401` without a key, `401` with a wrong key, and `2xx` with a valid key. Test this with a protected route registered **only in tests**; don't ship a dummy protected endpoint.
- [x] Multiple keys in `API_KEYS` all work.
- [x] The app refuses to start when `API_KEYS` is empty or missing, and a test covers this.
- [x] No API key value appears in logs, responses or the repo; `.env` is gitignored.
- [x] `/docs` shows the `X-API-Key` security scheme.
- [x] Tests pass in parallel: `pytest -n auto`, run from `api/`.
- [x] Code follows `CLAUDE.md`: functional style, immutable settings (frozen model), secure first.
- [x] Nothing is committed or pushed without asking the user first.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Implemented on branch `idelamadrid/BE-001-fastapi-scaffold`. All 14 tests pass via `uv run pytest -n auto`; runtime smoke-tested with uvicorn.
- **Settings:** frozen `pydantic-settings` model; `API_KEYS` parsed (comma-separated) and validated eagerly — missing/empty raises `ValidationError` in `create_app()`, so the app can never start with auth off. Loaded once via `lru_cache`.
- **Auth:** single `require_api_key` dependency (`security.py`) using `APIKeyHeader(auto_error=False)` + `secrets.compare_digest`; 401 body `{"detail": "Invalid or missing API key"}` + `WWW-Authenticate: ApiKey`. Keys never logged or echoed (tested).
- **OpenAPI:** FastAPI only emits a security scheme when a route uses it, so `create_app()` installs a custom `app.openapi` wrapper that always injects the `APIKeyHeader` (X-API-Key) scheme — the Authorize button in `/docs` works even before the first protected router ships. Covered by a dedicated test.
- **Protected route tested without shipping one:** test fixtures mount a `/__test-protected` probe router carrying `dependencies=[Depends(require_api_key)]`.
- **Decisions:** `/docs` and `/openapi.json` remain public (FastAPI default; the ticket only mandated `/health` and `/ping` as public *business* endpoints, and docs need to be reachable to authorize). No API-key value ever appears in responses — verified by test.
- Python 3.14.3 toolchain managed by `uv` (`requires-python >=3.12`); `uv.lock` generated; `.env`, `.venv/`, `__pycache__/` etc. added to root `.gitignore`.
- Not committed — per CLAUDE.md, awaiting explicit approval before any commit/push.
