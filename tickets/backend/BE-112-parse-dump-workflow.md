# BE-112: Build and export the parse_dump workflow

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend (mostly human steps in n8n)
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2, §9 · Milestone M8 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-041, BE-091, BE-111
- **Can run in parallel with:** M9–M11 tickets
- **Public endpoint?** no (the webhook is on `127.0.0.1` and verifies the HMAC signature)
- **Review size:** workflow JSON + ~40 lines (prompt file, README section), ~15 min

## Goal

A `parse_dump` workflow in the local n8n verifies the API's signature, asks an LLM to split the dump (Spanish and English, dates resolved in Mexico City), and returns JSON that passes `ParseDumpResult`. Its export is committed without credentials.

## Why this ticket exists

The M8 demo. Everything on the API side exists (BE-090, BE-091); this is the n8n side of the contract.

## Read first

- `RUNBOOK-n8n-setup.md` (BE-111): credentials, import/export.
- `integrations/n8n/README.md` (BE-041): signature verification snippet.
- `integrations/n8n/schemas/parse_dump.*.schema.json` (BE-091).

## Design

- **Pattern:** Pipeline: Webhook → verify signature (Code node) → LLM node with structured output → shape/validate (Code node) → Respond to Webhook.

## Packages

None new. The LLM provider key is an n8n credential (human step).

## Details

**Files:** `integrations/n8n/workflows/parse_dump.json` (exported, credentials removed), `integrations/n8n/prompts/parse_dump.md` (new: the prompt, versioned so changes are reviewable), `integrations/n8n/README.md` (changed: a `parse_dump` section).

**Workflow**

1. **Webhook** `POST /webhook/parse-dump`, response mode "using Respond to Webhook", raw body available.
2. **Verify** (Code): recompute HMAC-SHA256 over `timestamp + "." + rawBody` with the `todo-agent-hmac` credential; reject (401, empty body) when it differs or the timestamp is more than 5 minutes off.
3. **LLM** (provider node or HTTP node, your choice): prompt from `prompts/parse_dump.md`, structured output bound to `parse_dump.response.schema.json`.
4. **Shape** (Code): drop anything not in the schema; cap at 20 items.
5. **Respond**: `200` with the JSON.

**Prompt rules** (in `prompts/parse_dump.md`)

- Input language may be Spanish, English or mixed; keep titles in the user's language.
- Resolve relative dates ("next week", "el viernes") against `today` in `timezone`; output `YYYY-MM-DD`.
- Types: task, note, expense, reminder; money as integer cents with `MXN` unless USD is explicit.
- `sourceSpan` must be copied verbatim from the dump.
- Size XS–XL, energy, context only when reasonably clear; `firstStep` a tiny concrete action.
- Never invent items; when unsure, one task with low confidence.
- Send nothing but the dump text (epic §9).

**Human steps:** create the LLM credential; build the workflow in the UI; activate it; export it per the runbook; check for credentials before committing.

## Steps

1. Write the prompt file.
2. Build the workflow (human).
3. Export, scrub, commit-ready (human + agent review).
4. End-to-end run.

## Tests

- BE-041's `test_no_workflow_file_contains_credentials` passes with the new file.
- Manual checks below.

## Acceptance criteria

- [ ] With `DUMP_PARSER=n8n`, the M8 demo dump produces two tasks and one expense, dates in Mexico City
- [ ] A request with a wrong signature is rejected by n8n (401) and the API stores a fallback item
- [ ] Stopping n8n still stores a fallback item
- [ ] The exported workflow contains no credentials
- [ ] Round trip under 10 s for a three-item dump on your machine (note the time here)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make n8n-up && make n8n-check`, set `DUMP_PARSER=n8n`, restart the API, then in the web app press `/` and send:

```
call dentist next week, also buy cat food and pay gym 600
```

`#inbox` shows "Call dentist" (due next week), "Buy cat food", and an expense of $600.00 MXN. Then `make n8n-down` and send another dump: one "saved as is" item.

## Review guide

1. Prompt file: rules above, nothing extra sent.
2. Workflow JSON: no credential data; verify node present and first.

## Out of scope

- Voice and photo (transcribe, OCR) → EPIC-008 / Telegram capture phase.
- Expense routing to EPIC-002 → deferred.

## Notes / log
