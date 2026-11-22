# FE-045: What now? types and API client

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §8 · Milestone M10 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-106, FE-032
- **Can run in parallel with:** FE-049
- **Review size:** ~80 lines, 3 files, ~8 min

## Goal

`web/src/features/now/` has the request/response types and `askNow` / `recordAction` client functions.

## Why this ticket exists

The questions (FE-046), card (FE-047) and flow (FE-048) share these types; the client is tiny and testable alone.

## Read first

- `api/app/now/schemas.py` and router (BE-105, BE-106).
- `web/src/features/tasks/api/client.ts` (FE-032): `toTask`.

## Design

- **Pattern:** Facade over `request()`.

## Packages

None new.

## Details

**Files:** `web/src/features/now/model/types.ts` (new), `web/src/features/now/api/client.ts` + `.test.ts` (new).

```ts
export type Minutes = 5 | 15 | 30 | 60
export interface NowRequest { readonly energy: Energy | null; readonly availableMinutes: Minutes | null; readonly context: TaskContext | null }
export interface NowPick { readonly task: Task; readonly why: string }
export interface NowResult { readonly suggestionId: string | null; readonly pick: NowPick | null; readonly alternates: readonly NowPick[] }
export type SuggestionAction = 'started' | 'rerolled' | 'not-today'

createNowApi(fetchImpl?, base = '/api') => ({
  askNow: (req: NowRequest) => Promise<NowResult>,                                  // POST /now
  recordAction: (suggestionId: string, action: SuggestionAction) => Promise<void>,  // POST /now/{id}/action
})
```

## Steps

1. Types, client, mapping (`task`/`why` → `pick`, null-safe).
2. Tests.

## Tests

- `askNow maps a pick and alternates`
- `askNow maps nothing-fits to pick null`
- `recordAction posts the action`

## Acceptance criteria

- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Signed in, console: `const { nowApi } = await import('/src/features/now/api/client.ts'); await nowApi.askNow({energy:'low', availableMinutes:15, context:null})` → a pick with a why.

## Review guide

1. Null handling for nothing-fits.

## Out of scope

- UI → FE-046–048.

## Notes / log
