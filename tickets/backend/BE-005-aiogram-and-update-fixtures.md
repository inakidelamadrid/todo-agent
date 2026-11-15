# BE-005: Add aiogram and parse recorded update payloads

- **Status:** done (implemented and verified on branch `idelamadrid/BE-005-aiogram-and-update-fixtures`; not committed — awaiting user approval)
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2, §5.5
- **Assigned agent / harness / model:** pi coding agent / ollama / kimi-k3:cloud
- **Depends on:** none
- **Can run in parallel with:** BE-004, BE-010
- **Public endpoint?** no
- **Review size:** ~30 lines + 7 JSON fixtures, 3 files, ~10 min

## Goal

aiogram is installed and seven recorded Telegram update payloads parse into its typed `Update` model in tests.

## Why this ticket exists

This is the reviewer's first meeting with aiogram and with what a Telegram update looks like. Nothing else changes, so the dependency and the payload shapes can be understood on their own. Every later inbound test reuses these fixtures.

## Read first

- Confirm every aiogram name used here against https://docs.aiogram.dev/ (v3) before coding; do not rely on memory.
- Telegram's `Update` object: https://core.telegram.org/bots/api#update. An update has an `update_id` and exactly one payload field; we only use `message` and `callback_query`.
- `api/pyproject.toml`: how runtime and dev dependencies are split.

## Design

- **Pattern:** Parse, don't validate. Telegram's JSON is parsed once into a typed model at the edge; we never pick fields out of raw dicts.
- **Data flow:** fixture JSON → `aiogram.types.Update.model_validate(...)` → typed object.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `aiogram` | **new** | Typed Telegram models and (later) the Bot HTTP client | 3.32.0, MIT, released 2026-11-15, Python ≥3.11,<3.16. Its types are Pydantic models, which matches our stack. `python-telegram-bot` was rejected: LGPL-3.0. Hand-written `httpx` calls were rejected: we would re-type the whole Bot API. We use aiogram's types and `Bot` only, not its `Dispatcher`. |

## Details

**Files**

- `api/pyproject.toml`, `api/uv.lock` (changed): `uv add aiogram`, run inside `api/`.
- `api/tests/fixtures/telegram/` (new), seven files. All IDs are synthetic: the owner is user and chat `111111`, the stranger is `999999`, the bot is `222222`. No real names, usernames or message text.
  - `text.json`: a message with `text: "buy milk tomorrow"`.
  - `command.json`: `text: "/help"` with a `bot_command` entity at offset 0.
  - `voice.json`: a `voice` object (`file_id`, `duration`, `mime_type: "audio/ogg"`, `file_size`).
  - `photo.json`: a `photo` array of three sizes and `caption: "vault passport"`.
  - `document.json`: a `document` (`mime_type: "application/pdf"`, `file_size`), no caption.
  - `callback_query.json`: a `callback_query` with `id`, `from`, `message` and `data: "placeholder"`.
  - `stranger_text.json`: like `text.json` but from user `999999`.
- `api/tests/telegram_fixtures.py` (new): `load_payload(name: str) -> dict[str, Any]` and `load_update(name: str) -> Update`.
- `api/tests/test_telegram_fixtures.py` (new).

## Steps

1. Check aiogram on PyPI again (version, licence) and note it in the log.
2. `uv add aiogram` in `api/`.
3. Write the seven fixtures by hand from the Bot API documentation.
4. Add the loader and the tests.

## Tests

- `test_every_fixture_parses` (parametrised over the seven names): `Update.model_validate` succeeds and `update_id` is an int.
- `test_fixtures_use_only_synthetic_ids`: every `from.id` is `111111` or `999999`.
- `test_update_ids_are_unique_across_fixtures`.

## Acceptance criteria

- [x] `aiogram` is a runtime dependency in `api/pyproject.toml` and the lockfile is updated
- [x] The seven fixtures exist and parse
- [x] No fixture contains a real ID, name or token
- [x] No application code under `api/app/` imports aiogram yet
- [x] Tests pass (`make api-test`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

Open two fixtures and compare them with the Bot API page linked above.

## Review guide

Read the diff in this order, and check:

1. `api/pyproject.toml`: one new line, in runtime dependencies.
2. The fixtures: do they look like the documented `Update` shape? Are all IDs synthetic?
3. `telegram_fixtures.py`: a loader and nothing else.

Things that should *not* be in the diff: changes under `api/app/`; a `Dispatcher`; network calls.

## Out of scope

- Turning an `Update` into our own type → BE-006.
- Sending anything → BE-018, BE-019.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/BE-005-aiogram-and-update-fixtures`. PyPI re-checked: aiogram **3.32.0, MIT, Python >=3.11,<3.16** — matches the ticket's evaluation.
- Seven hand-written fixtures under `api/tests/fixtures/telegram/` (synthetic IDs 111111/999999/222222, unique update_ids 700000001–7); loader in `tests/telegram_fixtures.py`; nothing under `app/` imports aiogram.
- **Incident fixed (BE-004 bug exposed):** `test_settings_telegram.py` built bare `Settings()`, which reads the developer's real `api/.env`. Once the dev completed the manual Telegram setup, those tests failed **and dumped the real token into pytest output** (local only, nothing uploaded; recommend `/revoke` + rotate in BotFather if desired). Fix: every construction in that test file now uses `Settings(_env_file=None)`; module docstring documents the rule.
- `make api-test` → 99 passed.
