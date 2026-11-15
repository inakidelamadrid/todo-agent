# BE-027: GET and PATCH /settings/notifications

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §9 Frontend, §5.3
- **Assigned agent / harness / model:**
- **Depends on:** BE-026
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~12 min

## Goal

The web app can read and change quiet hours, pause, caps and grouping through a protected endpoint.

## Why this ticket exists

It is the API half of the notification settings screen (FE-003 to FE-005), and the first consumer of the policy repository.

## Read first

- `api/app/bills/schemas.py`: camelCase aliases with `alias_generator=to_camel`.
- `api/app/bills/router.py`: a PATCH that applies only the fields sent.
- `api/tests/test_bills_api.py`: the auth tests every protected route gets.

## Design

- **Pattern:** Thin controller: validate → repository → schema.
- **Data flow:** request → `NotificationSettingsPatch` → `get_policy` → `model_copy(update=…)` → `save_policy` → `NotificationSettingsOut`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/notifications/schemas.py` (new), `api/app/notifications/router.py` (new).
- `api/app/main.py` (changed): mount with `dependencies=[Depends(require_api_key)]`.
- `api/tests/test_notification_settings_api.py` (new).

**Endpoints** (both require `X-API-Key`)

`GET /settings/notifications` → `200`

```json
{
  "quietStart": "20:00",
  "quietEnd": "08:00",
  "timezone": "America/Mexico_City",
  "pausedUntil": null,
  "urgentCategories": [],
  "caps": {},
  "groupingWindowMinutes": 5
}
```

`PATCH /settings/notifications` with any subset of those fields → `200` with the full object.

**Validation (`422` otherwise)**

| Field | Rule |
|---|---|
| `quietStart`, `quietEnd` | `HH:MM`, 24-hour |
| `timezone` | must be in `zoneinfo.available_timezones()` |
| `pausedUntil` | ISO 8601 with offset, or `null` to resume; stored as UTC |
| `urgentCategories` | up to 20 strings, each `^[a-z][a-z0-9_-]{0,29}$` |
| `caps` | up to 20 entries; keys as above; values 0–50 |
| `groupingWindowMinutes` | 0–120 |

Unknown fields → `422` (`extra="forbid"`). An empty PATCH body → `200`, unchanged.

## Steps

1. Schemas with validators.
2. The two routes.
3. Mount the router.
4. Tests.

## Tests

- `test_get_requires_api_key`, `test_get_rejects_wrong_key`, `test_patch_requires_api_key`, `test_patch_rejects_wrong_key`
- `test_get_returns_defaults`
- `test_patch_changes_only_sent_fields`
- `test_patch_paused_until_null_resumes`
- `test_patch_rejects_bad_time`, `..._unknown_timezone`, `..._cap_over_50`, `..._unknown_field`
- `test_response_is_camel_case`

## Acceptance criteria

- [ ] Both routes reject requests without a valid API key
- [ ] JSON is camelCase in both directions
- [ ] Each rule in the validation table has a failing test case
- [ ] `pausedUntil` is stored and returned as UTC
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With `make api-dev` running, call `GET /settings/notifications` from the docs page at `http://127.0.0.1:8000/docs` after authorising with your key, then PATCH `{"quietStart": "21:00"}` and GET again.

## Review guide

Read the diff in this order, and check:

1. `schemas.py`: the validation table, rule by rule.
2. `router.py`: no logic beyond load, copy, save.
3. `main.py`: the router is mounted with the API key dependency.

Things that should *not* be in the diff: frontend code; Telegram code.

## Out of scope

- The settings screen → FE-003 to FE-005.
- `/pause` from Telegram → BE-028.

## Notes / log

The agent adds progress notes, decisions and open questions here.
