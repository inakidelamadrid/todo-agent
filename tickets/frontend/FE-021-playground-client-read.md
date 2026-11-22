# FE-021: Playground client, part 1: probe, updates, templates; connect the gate

- **Status:** review (implemented on branch `idelamadrid/FE-021` with FE-021, FE-022, FE-027, FE-028 and FE-029; synced with main after BE-078 and BE-079 merged; not committed, awaiting user approval)
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** FE-020, BE-068, BE-071, BE-078
- **Can run in parallel with:** FE-023, FE-025, FE-027
- **Review size:** ~80 lines, 4 files plus tests, ~12 min

## Goal

Typed client functions for the read-only playground endpoints exist, and the shell's gate comes from the real probe.

## Why this ticket exists

Types and client before any panel is wired, per the house order. This ticket also fixes one trap: the app-wide `403` handler shows the 'not allowed' screen for the whole app (FE-016), which must not happen when a playground call is refused.

## Read first

- `web/src/lib/api.ts`: `createRequest`, `OnAuthFailure`.
- `web/src/features/auth/authFailure.ts`: what `403` does today.
- `web/src/features/bills/api/client.ts` and its test: the typed client pattern.

## Design

- **Pattern:** Typed client as a factory over the shared request (`createPlaygroundApi(request)`).
- **Data flow:** panel → `playgroundApi.listUpdates()` → `request('GET', '/admin/telegram/updates')` → typed result.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/types.ts` (new), matching the API's camelCase:
  - `UpdateLogItem { updateId: number; kind: string; route: string; status: 'received' | 'processed' | 'failed'; receivedAt: string; playground: boolean }`
  - `TemplateInfo { name: string; fields: readonly string[] }`
  - `TemplatePreview { html: string; length: number }`
- `web/src/features/playground/api.ts` (new): `createPlaygroundApi(request)` with `probe()`, `listUpdates(filters?: { limit?: number; status?: string; route?: string })`, `listTemplates()`, `previewTemplate(template, data)`.
- `web/src/features/playground/request.ts` (new): the playground's own `request`, built with `createRequest(fetch, '/api', getSessionToken, onAuthFailure)` where `onAuthFailure` forwards **only `401`** to `handleAuthFailure`. A `403` here means 'not an admin' for this area and must not flip the whole app to the not-allowed screen.
- `web/src/App.tsx` or a small `PlaygroundScreen.tsx` (changed/new): calls `probe()` on mount, maps the result with `gateFromProbe`, passes `gate` and `onRetry` to the shell.
- `web/src/features/playground/api.test.ts` (new).

Filters are sent as query parameters; they contain no personal data.

## Steps

1. Types.
2. Client with tests against a fake `fetch`.
3. The playground request with the `401`-only handler.
4. Connect the probe to the gate.

## Tests

- `test_probe_ok_and_statuses`: `200` → ok; `404`, `403` → not ok with the status.
- `test_list_updates_builds_query_and_parses_items`.
- `test_list_templates_parses`.
- `test_preview_posts_template_and_data`.
- `test_playground_403_does_not_trigger_global_forbidden`.
- `test_playground_401_still_ends_the_session`.

## Acceptance criteria

- [ ] The four client functions are typed and tested
- [ ] With the switch off the shell shows 'switched off'; as a non-admin calling the probe directly it shows 'for admins'
- [ ] A `403` from a playground endpoint does not show the app-wide not-allowed screen
- [ ] A `401` still signs out as before
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-test`: green.
2. Playground on, as admin: `#playground` shows the tabs. Set `TELEGRAM_PLAYGROUND_ENABLED=false`, restart the API, reload: 'switched off'.

## Review guide

Read the diff in this order, and check:

1. `request.ts`: which statuses reach the global handler? Only `401`.
2. `api.ts`: one function per endpoint, no logic.

Things that should *not* be in the diff: Panels, stores, the write endpoints.

## Out of scope

- Test-message client → FE-022; explain and replay client → FE-030.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `types.ts` now holds the wire types; `updateLog.ts` re-exports `UpdateLogItem`/`UpdateStatus` so FE-023 code is unchanged.
- `request.ts`: `forwardUnauthorizedOnly(handle)` + `createPlaygroundRequest()`; a playground 403 never reaches the app-wide forbidden handler.
- `api.ts`: `createPlaygroundApi(request)`; `probe()` never throws (network error → status 0); pure `updatesQuery` sends only set filters.
- `PlaygroundScreen.tsx`: `usePlaygroundGate` probes on mount; Try again re-probes. The Updates tab still shows fixtures (FE-024).
- BE-078 is merged and its routes and shapes match the client. `listUpdates` still follows BE-071's ticket (not merged); FE-024 wires it.
