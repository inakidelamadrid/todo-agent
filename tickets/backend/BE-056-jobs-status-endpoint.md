# BE-056: GET /jobs/status

- **Status:** todo
- **Workspace:** backend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-052, BE-054
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~10 min

## Goal

A protected endpoint reports whether the worker and scheduler are alive and how many jobs failed recently.

## Why this ticket exists

Background processes fail silently by nature. This gives the web app (FE-008) and you one place to check.

## Read first

- `api/app/telegram/status.py` (BE-043): the same kind of endpoint.
- `api/tests/test_bills_api.py`: the auth tests.

## Design

- **Pattern:** Thin controller over a pure classification function.
- **Data flow:** request → read `jobs:heartbeat` + `count_failures_since` → `classify_heartbeat` → `JobsStatus`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/jobs/status.py` (new): schema, pure function, route. `api/app/main.py` (changed): mount with `require_api_key`.
- `api/tests/test_jobs_status_api.py` (new).

**Pure function**

```python
def classify_heartbeat(last: datetime | None, now: datetime) -> Literal["ok", "stale", "never"]
```
`None` → `never`; older than 3 minutes → `stale`; else `ok`.

**Response** (`200`, requires `X-API-Key`)

```json
{
  "heartbeat": "ok",
  "lastHeartbeatAt": "2026-11-15T15:04:00Z",
  "failures24h": 0,
  "schedules": [{"job": "system.heartbeat", "cron": "* * * * *"}, {"job": "system.cleanup", "cron": "30 3 * * *"}]
}
```

If Redis is unreachable: `heartbeat: "stale"`, `lastHeartbeatAt: null`, still `200`.

## Steps

1. `classify_heartbeat` with tests.
2. Schema and route.
3. Mount.
4. Auth and content tests.

## Tests

- `test_status_requires_api_key`, `test_status_rejects_wrong_key`
- `test_classify_heartbeat_ok_stale_never`
- `test_status_reports_failures_in_last_24h`
- `test_status_lists_schedules`
- `test_redis_down_reports_stale_and_200`

## Acceptance criteria

- [ ] The route requires a valid API key
- [ ] It distinguishes "never ran" from "stopped"
- [ ] It never returns job payloads or error messages
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With worker and scheduler running, call the endpoint from `/docs`: `heartbeat` is `ok`. Stop the worker and wait three minutes: `stale`.

## Review guide

Read the diff in this order, and check:

1. `classify_heartbeat`: the three cases.
2. `main.py`: mounted with the API key dependency.

Things that should *not* be in the diff: frontend; alerting.

## Out of scope

- The status line in the app → FE-008.
- Alerts → BE-057.

## Notes / log

The agent adds progress notes, decisions and open questions here.
