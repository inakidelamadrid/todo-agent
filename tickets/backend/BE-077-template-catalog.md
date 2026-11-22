# BE-077: Template catalog: names and required fields (pure)

- **Status:** in review
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** BE-020
- **Can run in parallel with:** BE-065 to BE-076
- **Public endpoint?** no
- **Review size:** ~40 lines, 1 file plus tests, ~8 min

## Goal

`list_templates()` returns every template name with the data fields it needs, derived from the template text itself.

## Why this ticket exists

The preview tool needs to offer the templates and show which fields to fill. Deriving the fields from the text (instead of a second hand-kept list) means the catalog cannot go out of date.

## Read first

- `api/app/telegram/templates.py` (BE-020): `TEMPLATES`, `render`.
- `string.Formatter().parse` in the standard library docs.

## Design

- **Pattern:** Plain pure function over an immutable table.
- **Data flow:** `TEMPLATES` → `string.Formatter().parse(text)` → `TemplateInfo(name, fields)`.

## Packages

None new. Standard library and what is already installed.

## Details

**File:** `api/app/telegram/templates.py` (changed).

```python
class TemplateInfo(BaseModel):      # frozen
    name: str
    fields: tuple[str, ...]         # in order of first appearance, no duplicates

def template_fields(text: str) -> tuple[str, ...]       # pure
def list_templates(lang: str = DEFAULT_LANG) -> tuple[TemplateInfo, ...]   # pure, sorted by name
```

`template_fields("I don't know <code>/{command}</code>.")` → `("command",)`. Escaped braces (`{{`, `}}`) are not fields.

## Steps

1. `template_fields` with tests.
2. `list_templates`.
3. Run `make api-test`.

## Tests

- `test_fields_in_order_without_duplicates`.
- `test_no_fields_for_plain_text`.
- `test_escaped_braces_are_not_fields`.
- `test_list_templates_covers_every_template_sorted`.
- `test_every_listed_template_renders_with_its_fields_filled`: guards against a mismatch with `render`.

## Acceptance criteria

- [ ] `list_templates` returns every template with its fields
- [ ] Fields come from the template text, not a separate list
- [ ] Every listed template renders when its fields are supplied
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `cd api && uv run pytest tests/test_telegram_templates.py -q`: green.

## Review guide

Read the diff in this order, and check:

1. Is there any hand-written list of fields? There should be none.

Things that should *not* be in the diff: Routes, new templates.

## Out of scope

- The endpoints → BE-078.

## Notes / log

The agent adds progress notes, decisions and open questions here.
