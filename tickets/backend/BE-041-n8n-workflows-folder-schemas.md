# BE-041: integrations/n8n: exported schemas and workflow folder

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.4
- **Assigned agent / harness / model:**
- **Depends on:** BE-036
- **Can run in parallel with:** BE-037, BE-038
- **Public endpoint?** no
- **Review size:** ~60 lines + README, 3 files, ~8 min

## Goal

The repository holds the JSON Schemas n8n must return and a place, with instructions, for versioned workflow exports.

## Why this ticket exists

The contract with n8n has two sides. The API side is tested Python; the n8n side is a visual workflow that lives outside the repo unless it is exported. Generated schema files give the workflow author something exact to target, and a test keeps them in step with the Pydantic models.

## Read first

- `api/app/n8n/schemas.py`.
- Pydantic `model_json_schema(by_alias=True)`.

## Design

- **Pattern:** Generated artefact guarded by a test (the test fails when the committed file is stale).
- **Data flow:** Pydantic models → `export_n8n_schemas.py` → `integrations/n8n/schemas/*.json`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/scripts/export_n8n_schemas.py` (new): writes `transcribe.response.schema.json` and `ocr.response.schema.json`. `Makefile`: `n8n-schemas`.
- `integrations/n8n/README.md` (new), `integrations/n8n/schemas/` (generated), `integrations/n8n/workflows/.gitkeep`.
- `api/tests/test_n8n_schema_export.py` (new).

**README contents**

- The contract: endpoint paths, request body, the `X-Timestamp` / `X-Signature` headers and how to verify them in an n8n Code node (recompute HMAC-SHA256 over `timestamp + "." + rawBody`; reject when it differs or the timestamp is more than 5 minutes old).
- n8n never writes to the API's database; it only answers the request (architecture B).
- How to export a workflow from n8n to `workflows/<name>.json`, and the rule: **remove credentials before committing** (exports can embed them).

**Human steps.** Building and exporting the two workflows in n8n is yours; the agent prepares the folder and the contract only.

## Steps

1. The export script and make target.
2. Generate and commit the two schema files.
3. The staleness test.
4. The README.

## Tests

- `test_committed_schemas_match_models`: regenerate in memory and compare with the files.
- `test_schemas_forbid_additional_properties`
- `test_no_workflow_file_contains_credentials`: scans `workflows/*.json` for a `credentials` key with data; passes on an empty folder.

## Acceptance criteria

- [ ] Changing a model without re-running `make n8n-schemas` fails the test suite
- [ ] The README documents signature verification with the 5-minute window
- [ ] A committed workflow containing credentials fails the test suite
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make n8n-schemas
```

```bash
git status --short integrations/
```

No changes expected after a fresh generation.

## Review guide

Read the diff in this order, and check:

1. The generated schema files against BE-036's table.
2. The README's verification snippet: same bytes as `sign_request` in BE-038.

Things that should *not* be in the diff: actual workflow JSON (human step); feature schemas.

## Out of scope

- `parse_dump`, `parse_expense`, `extract_document` contracts → EPIC-003, 002, 006.

## Notes / log

The agent adds progress notes, decisions and open questions here.
