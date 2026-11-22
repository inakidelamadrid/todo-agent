# BE-020: Message templates with central HTML escaping

- **Status:** done
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3
- **Assigned agent / harness / model:** Engine / Claude Code / claude-opus-5-5
- **Depends on:** none
- **Can run in parallel with:** BE-004 to BE-019
- **Public endpoint?** no
- **Review size:** ~100 lines, 2 files, ~12 min

## Goal

`render(template, data)` returns the final message text, with every piece of data HTML-escaped in one place.

## Why this ticket exists

Message text is user-influenced (a task title can contain `<` or `&`). Telegram's HTML mode would reject or misrender it, and unescaped data is an injection risk. If escaping lives in one function, no feature can forget it.

## Read first

- https://core.telegram.org/bots/api#html-style: the tags Telegram allows.
- `html.escape` in the standard library.
- `web/src/features/bills/model/schedule.ts`: pure formatting functions as a style reference.

## Design

- **Pattern:** Pure function over an immutable table of templates.
- **Data flow:** `(template name, data, lang)` → escape every value → fill the template → `str`.

## Packages

None new. Standard library and what is already installed.

Hand-written instead of a package: the template table and a 10-line `render`. Jinja2 was considered and rejected: these are one-line messages, and a full template engine adds an autoescape configuration to get wrong.

## Details

**Files**

- `api/app/telegram/templates.py` (new).
- `api/tests/test_telegram_templates.py` (new).

**Table.** `TEMPLATES: Mapping[str, Mapping[str, str]]`: template name → language → text using `str.format` fields. Immutable. English only for now; the language level stays so Spanish can be added without changing callers.

| Name | English text |
|---|---|
| `help` | `<b>What I can do</b>` followed by one line per command and its description |
| `not_available` | `That isn't available yet.` |
| `unknown_command` | `I don't know <code>/{command}</code>. Try /help.` |
| `unsupported` | `I can't read that kind of message yet.` |
| `working` | `Working on it…` |
| `expired_button` | `That button has expired.` |

**Function (pure)**

```python
DEFAULT_LANG = "en"

def render(template: str, data: Mapping[str, str] | None = None, lang: str = DEFAULT_LANG) -> str
```

- Every value in `data` passes through `html.escape(value, quote=False)` before formatting. Template text itself is trusted.
- Unknown template → `UnknownTemplate(template)`. Missing data field → `MissingTemplateData(template, field)`. Unknown language → falls back to `DEFAULT_LANG`.
- Result longer than 4096 characters → `ValueError`.

**Tone.** Calm and short, per `Epics/README.md` conventions: no exclamation marks, no guilt, no emoji beyond a single `✓` where a later template needs it.

## Steps

1. Write the table.
2. Write `render` and the two error types.
3. Tests, including the escaping cases.

## Tests

- `test_render_help_lists_every_command`: every key of `routing.COMMANDS` except `start` appears.
- `test_values_are_escaped`: `{"command": "<b>&"}` → `&lt;b&gt;&amp;` in the output.
- `test_template_markup_is_not_escaped`
- `test_unknown_template_raises`
- `test_missing_field_raises_with_field_name`
- `test_unknown_language_falls_back_to_english`
- `test_overlong_result_raises`

## Acceptance criteria

- [ ] `render` is the only place message text is assembled
- [ ] Every data value is escaped
- [ ] The module has no I/O and no aiogram import
- [ ] Every template named by a handler in BE-015 exists
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `render`: find the escape call; can any value bypass it?
2. The template texts: are they what you want the bot to say?

Things that should *not* be in the diff: sending; Spanish texts; feature templates (each epic adds its own rows).

## Out of scope

- Sending rendered text → BE-021.
- Buttons → BE-023.

## Assumptions

- English only, as answered (question 4).

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Help lines follow the BotFather command list in EPIC-008 §5.1.
- `MESSAGE_TEXT_MAX_CHARS` is defined here too, because BE-018 (which also defines it in `sender.py`) is not merged yet. Fold into one constant once both land.
- **For BE-021:** BE-015's `_unknown_command` returns `Reply(template="unknown_command")` with no data, so `render` raises `MissingTemplateData`. It should pass `{"command": update.command}`.
- Extra tests: braces in values are not re-formatted, every handler's template exists, the table is immutable.
