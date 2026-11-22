# FE-002: Extract the shared API request helper (no behaviour change)

- **Status:** done (committed on `idelamadrid/FE-002`; not pushed)
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §9 Frontend
- **Assigned agent / harness / model:** Claude Code / claude-fable-5-2
- **Depends on:** none
- **Can run in parallel with:** every BE ticket
- **Review size:** ~80 lines moved, 3 files, ~10 min

## Goal

`ApiError`, `isApiError`, `toFieldErrors` and the `request` helper live in `web/src/lib/api.ts`, and the bills client imports them from there.

## Why this ticket exists

The notification settings client (FE-003) needs the same request and error handling the bills client has. Moving it first, alone, keeps this diff a pure move that can be reviewed by checking nothing changed, instead of hiding a refactor inside a feature.

## Read first

- `web/src/features/bills/api/client.ts`: lines 12–50 hold the generic parts; `createBillsApi` builds on a private `request`.
- `web/src/features/bills/api/client.test.ts`.

## Design

- **Pattern:** Refactor before feature. Facade: one `createRequest(fetchImpl, base)` under every typed client.
- **Data flow:** `createRequest(fetch, '/api')` → `request<T>(method, path, body?)` → parsed JSON or `ApiError`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/lib/api.ts` (new): `Fetch` type, `FieldErrors`, `ApiError`, `isApiError`, `toFieldErrors`, and `createRequest(fetchImpl, base)` returning the `request` function that currently lives inside `createBillsApi`.
- `web/src/features/bills/api/client.ts` (changed): imports them; re-exports `ApiError`, `isApiError`, `FieldErrors`, `toFieldErrors` so existing imports elsewhere keep working.
- `web/src/lib/api.test.ts` (new): the generic tests moved from `client.test.ts`.

**Rules**

- Move code, do not rewrite it. The body of each moved function must be character-for-character the same, apart from imports.
- `createBillsApi(fetchImpl, base)` keeps its signature and its returned shape.
- No component or store file changes.

## Steps

1. Create `lib/api.ts` by moving the generic code.
2. Point the bills client at it and add the re-exports.
3. Move the generic tests.
4. Run tests and build.

## Tests

- Existing bills client and store tests pass unchanged.
- `request turns a 422 into ApiError with field errors` (moved).
- `request turns a network failure into ApiError` (moved, if present today).

## Acceptance criteria

- [ ] `git diff --stat` shows only the three files above
- [x] No file outside `web/src/lib/` and `web/src/features/bills/api/` changes
- [ ] The bills view behaves exactly as before in the browser
- [x] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make web-test
```

```bash
make web-build
```

Open the app, add and mark a bill paid: unchanged.

## Review guide

Read the diff in this order, and check:

1. `lib/api.ts` side by side with the removed lines: a move, not a rewrite.
2. The re-exports in the bills client.
3. No behaviour change anywhere.

Things that should *not* be in the diff: new endpoints, new types, a data-fetching library.

## Out of scope

- The notifications client → FE-003.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/FE-002`. The generic block and the body of `request` were moved by script, character for character; only `export` on `Fetch`, the `createRequest` wrapper and its doc comment are new.
- Four files, not three: the ticket lists `api.ts`, `client.ts` and `api.test.ts`, and moving the generic tests also edits `client.test.ts`. That criterion stays unchecked.
- The moved tests call `request` directly instead of going through the bills client; assertions are the same.
- `make web-test` → 50 passed (same count as before); `make web-build` passes.
- Not checked in the browser: the bills view now sits behind sign-in, which needs the owner's Google account.
