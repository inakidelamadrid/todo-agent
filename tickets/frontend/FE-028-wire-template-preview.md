# FE-028: Wire the template preview to the API

- **Status:** review (implemented on branch `idelamadrid/FE-021` with FE-021, FE-022, FE-027, FE-028 and FE-029; synced with main after BE-078 and BE-079 merged; not committed, awaiting user approval)
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** FE-021, FE-027
- **Can run in parallel with:** FE-024, FE-026, FE-029
- **Review size:** ~50 lines, 3 files plus tests, ~8 min

## Goal

The Templates tab lists the real templates and previews them through the API's real renderer.

## Why this ticket exists

Small wiring ticket; the panel and client exist.

## Read first

- `TemplatePreviewPanel` (FE-027), `createPlaygroundApi` (FE-021).
- `useUpdateLogStore` (FE-024) for the store shape.

## Design

- **Pattern:** Small Zustand store with explicit status.
- **Data flow:** tab opens → `listTemplates` → select → fields → **Preview** → `previewTemplate` → panel.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/useTemplatesStore.ts` (new): `{ templates; selected; data; preview; status; previewStatus; error; load(); select(name); setField(name, value); runPreview() }`. Selecting a template resets `data` and `preview`. The store is shared with the Test message tab (FE-029).
- `web/src/features/playground/TemplatesTab.tsx` (new).
- Shell usage (changed).
- `useTemplatesStore.test.ts` (new).

A `422` naming a missing field maps to that field's inline error.

## Steps

1. Store with tests.
2. Tab.
3. Plug in and check.

## Tests

- `test_load_lists_templates`.
- `test_select_resets_data_and_preview`.
- `test_run_preview_sets_preview`.
- `test_missing_field_error_maps_to_the_field`.

## Acceptance criteria

- [ ] The tab lists the API's templates
- [ ] A preview shows the API's rendered text
- [ ] Changing template clears the previous preview
- [ ] Errors show in place
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Templates tab: pick `unknown_command`, enter `<b>x</b>`, **Preview**: the bubble shows the literal `<b>x</b>` inside code, and the source shows it escaped.

## Review guide

Read the diff in this order, and check:

1. The store: is state reset on select?
2. Is the preview text ever built on the client? It must come from the API.

Things that should *not* be in the diff: Sending.

## Out of scope

- Send test message → FE-029.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `useTemplatesStore.ts`: `createTemplatesStore(api)` factory; loads once (`force` for Try again); `select` clears data and preview; `setField` clears that field's error.
- `TemplatesTab.tsx` loads on mount; plugged into the shell via `PlaygroundScreen`.
- FE-024's store didn't exist yet, so the shape follows `useBillsStore`.
- Checked in Chrome with a fake API matching BE-078's examples (`unknown_command` + `<b>x</b>` shows literal text in code).
