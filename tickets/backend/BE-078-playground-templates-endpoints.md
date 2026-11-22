# BE-078: `GET /admin/telegram/templates` and `POST …/templates/preview`

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** BE-068, BE-069, BE-077
- **Can run in parallel with:** BE-071 to BE-076
- **Public endpoint?** no
- **Review size:** ~60 lines, 2 files plus tests, ~10 min

## Goal

An admin can list the templates and render one with sample data, seeing the exact text Telegram would receive.

## Why this ticket exists

Lets you check wording and escaping without sending anything. It calls the real `render`, so what you see is what would be sent.

## Read first

- `api/app/telegram/templates.py`: `render` and its error types.
- `api/app/telegram/playground/router.py`.

## Design

- **Pattern:** Plain routes over pure functions.
- **Data flow:** `POST preview` → `render(template, data)` → `{html, length}`; `record_action(…, "template_preview", …)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files:** `api/app/telegram/playground/router.py`, `schemas.py` (changed).

**`GET /admin/telegram/templates`** → `200 {"templates": [{"name": "help", "fields": []}, {"name": "unknown_command", "fields": ["command"]}]}`

**`POST /admin/telegram/templates/preview`**

```json
{"template": "unknown_command", "data": {"command": "<b>x</b>"}}
```

| Case | Status | Body |
|---|---|---|
| Rendered | `200` | `{"html": "I don't know <code>/&lt;b&gt;x&lt;/b&gt;</code>. Try /help.", "length": 58}` |
| Unknown template | `404` | `{"detail": "Unknown template"}` |
| Missing field | `422` | detail names the missing field |
| Too long (> 4096) | `422` | detail says so |

Limits: at most 20 data keys; each key ≤ 40 chars, each value ≤ 1000 chars. The data is not stored or logged.

Buttons are not previewed: templates carry none of their own (handlers attach them, BE-023). That comes with the callback decoder tool.

## Steps

1. Schemas with the limits.
2. Both routes.
3. Tests.
4. Run `make api-test`.

## Tests

- `test_templates_without_credentials_returns_401`: no credentials → `401`.
- `test_templates_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_templates_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_templates_when_playground_off_returns_404`: playground switched off → `404`.
- `test_preview_without_credentials_returns_401`: no credentials → `401`.
- `test_preview_as_non_admin_returns_403`: signed-in non-admin → `403`.
- `test_preview_as_machine_returns_403`: valid API key (machine) → `403`.
- `test_preview_when_playground_off_returns_404`: playground switched off → `404`.
- `test_templates_lists_names_and_fields`.
- `test_preview_escapes_data`.
- `test_preview_unknown_template_is_404`.
- `test_preview_missing_field_is_422_and_names_it`.
- `test_preview_enforces_data_limits`.
- `test_preview_records_an_action`.

## Acceptance criteria

- [ ] An admin can list templates and preview one
- [ ] The preview is the output of the real `render`, with data escaped
- [ ] The four guard cases hold on both routes
- [ ] Data limits are enforced
- [ ] A preview is recorded as a `template_preview` action
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make api-test`: green.
2. As admin: preview `unknown_command` with `command` = `<b>x</b>` → the tags come back escaped.

## Review guide

Read the diff in this order, and check:

1. Does the route call `render` and nothing else to produce text?
2. Are the limits in the schema?

Things that should *not* be in the diff: Sending, buttons, editing templates.

## Out of scope

- The panel → FE-027, FE-028.
- Sending the result → BE-079.

## Notes / log

The agent adds progress notes, decisions and open questions here.
