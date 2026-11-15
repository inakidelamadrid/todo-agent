# BE-036: Strict schemas for n8n transcribe and OCR responses

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.4
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-004 to BE-035
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files, ~8 min

## Goal

The JSON that n8n returns for transcription and OCR is defined as strict, frozen Pydantic models.

## Why this ticket exists

n8n calls an LLM, so its output is the least trustworthy data entering the API. A strict schema (unknown fields rejected, lengths bounded) turns "whatever the model said" into a typed value or a clean failure. Defining the contract first lets the n8n workflows and the client be built against it independently.

## Read first

- `api/app/bills/schemas.py`.
- Pydantic `extra="forbid"`: a response with a field we did not define is rejected instead of silently accepted.

## Design

- **Pattern:** Parse, don't validate, at the trust boundary.
- **Data flow:** n8n JSON → `TranscribeResult.model_validate` / `OcrResult.model_validate` → typed value or `ValidationError`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/n8n/__init__.py` (new, empty), `api/app/n8n/schemas.py` (new).
- `api/tests/test_n8n_schemas.py` (new).

**Models** (frozen, `extra="forbid"`, camelCase aliases)

| Model | Field | Rules |
|---|---|---|
| `TranscribeResult` | `text` | 0–10 000 characters, trimmed |
| | `language` | 2–8 characters, e.g. `es`, `en` |
| | `durationSeconds` | float, 0–3600 |
| `OcrResult` | `text` | 0–20 000 characters, trimmed |
| | `confidence` | float, 0–1 |

Example: `{"text": "comprar leche mañana", "language": "es", "durationSeconds": 3.2}`.

Only the two generic operations are defined here. `parse_dump`, `parse_expense` and `extract_document` return feature-shaped data and are defined by EPIC-003, EPIC-002 and EPIC-006.

## Steps

1. Write the two models.
2. Tests: one valid example each, then each rule violated.

## Tests

- `test_valid_transcribe_result_parses`
- `test_valid_ocr_result_parses`
- `test_unknown_field_is_rejected`
- `test_overlong_text_is_rejected`
- `test_confidence_out_of_range_is_rejected`
- `test_models_are_frozen`
- `test_json_is_camel_case`

## Acceptance criteria

- [ ] Both models reject unknown fields
- [ ] Every bound in the table has a failing test
- [ ] No HTTP code in this ticket
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The table against the models.
2. `extra="forbid"` on both.

Things that should *not* be in the diff: the client, HMAC, feature-specific schemas.

## Out of scope

- Calling n8n → BE-037, BE-038.
- Exporting JSON Schema files → BE-041.

## Notes / log

The agent adds progress notes, decisions and open questions here.
