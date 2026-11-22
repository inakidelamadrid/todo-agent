# BE-068: Playground switch, `APP_ENV`, and the guarded `/admin/telegram` router

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-066
- **Can run in parallel with:** BE-069
- **Public endpoint?** no
- **Review size:** ~60 lines, 4 files plus tests, ~12 min

## Goal

A router at `/admin/telegram` exists behind `require_admin` and a switch. With the switch off every route under it answers `404`; the app refuses to start with the switch on in production. One probe route proves the guards.

## Why this ticket exists

All later playground endpoints mount on this router, so they inherit both guards and none can forget them. The switch and the production rule (epic question 10: development only) are introduced here, alone, where they can be read without any tool logic around them.

## Read first

- `api/app/main.py`: `create_app` and its start-up check for Clerk.
- `api/app/settings.py`: how a start-up rule is expressed.
- `api/app/routes/me.py`: a small router.

## Design

- **Pattern:** Fail-closed guard as a router-level dependency. New endpoints are protected by where they are mounted, not by remembering a decorator.
- **Data flow:** request → `require_admin` (`401`/`403`) → `require_playground` (`404` when off) → route.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/settings.py` (changed): `app_env: Literal["development", "production"] = "development"` and `telegram_playground_enabled: bool = False`. Pure helper `playground_allowed(settings) -> bool`: enabled and not production.
- `api/app/telegram/playground/__init__.py` (new, empty) and `api/app/telegram/playground/router.py` (new):

```python
def require_playground(settings: Annotated[Settings, Depends(get_settings)]) -> None:
    if not playground_allowed(settings):
        raise HTTPException(status_code=404, detail="Not found")

playground_router = APIRouter(
    prefix="/admin/telegram", tags=["telegram-playground"],
    dependencies=[Depends(require_admin), Depends(require_playground)],
)

@playground_router.get("/playground")
def probe() -> PlaygroundInfo: ...        # {"enabled": true}
```

  If `api/app/telegram/__init__.py` does not exist yet, create it empty.
- `api/app/main.py` (changed): `create_app` raises `RuntimeError("TELEGRAM_PLAYGROUND_ENABLED must be false when APP_ENV is production")` in that case; mounts `playground_router`.
- `api/.env.example` (changed): `APP_ENV=development` and `TELEGRAM_PLAYGROUND_ENABLED=false`, each with a comment.

Authentication runs before the switch on purpose: an anonymous caller gets `401` whether the playground is on or off, so the switch reveals nothing.

## Steps

1. Add the two settings and `playground_allowed`.
2. Write the router with the probe.
3. Add the start-up rule and mount the router.
4. Run `make api-test`.

## Tests

- `test_probe_without_credentials_returns_401`: no credentials → `401`.
- `test_probe_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_probe_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_probe_when_playground_off_returns_404`: playground switched off → `404`.
- `test_probe_as_admin_returns_enabled_true`.
- `test_app_refuses_to_start_with_playground_on_in_production`.
- `test_playground_allowed_truth_table`: the four combinations of switch and environment.

## Acceptance criteria

- [ ] `GET /admin/telegram/playground` returns `{"enabled": true}` only to an admin with the switch on
- [ ] Non-admin and machine get `403`, no credentials `401`, switch off `404`
- [ ] The app does not start with the switch on and `APP_ENV=production`
- [ ] Both settings are documented in `api/.env.example`, off by default
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. Set `TELEGRAM_PLAYGROUND_ENABLED=true` in `api/.env`, `make api-dev`: `curl -i http://127.0.0.1:8000/admin/telegram/playground` → `401`; with a valid `X-API-Key` → `403`.
3. Add `APP_ENV=production` and restart: the app exits with the message. Remove it again.

## Review guide

Read the diff in this order, and check:

1. `router.py`: are both dependencies on the router, not on the route?
2. `main.py`: does the start-up message name variables only?
3. `settings.py`: are both defaults the safe ones?

Things that should *not* be in the diff: Any tool endpoint, database access, the web app.

## Out of scope

- Tool endpoints → BE-071, BE-074, BE-076, BE-078, BE-079.
- Recording actions → BE-069.

## Assumptions

- `APP_ENV` is the way the app knows it is in production (epic question 10, assumed). Hosting may replace it later.

## Notes / log

The agent adds progress notes, decisions and open questions here.
