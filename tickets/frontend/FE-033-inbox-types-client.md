# FE-033: Inbox types and API client (dump, list)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2, §5.3 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-096
- **Can run in parallel with:** FE-035, FE-036
- **Review size:** ~90 lines, 3 files, ~8 min

## Goal

`web/src/features/inbox/` has the inbox types (mirroring BE-089) and a client with `postDump` and `listInbox`.

## Why this ticket exists

Quick add (FE-037) posts dumps and the Inbox screen (FE-041) lists items. Both need the shared shape first. Action calls (accept, snooze, accept all) are added by the tickets that use them, so this stays small.

## Read first

- `api/app/inbox/schemas.py` (BE-089): field names and the payload union.
- `web/src/features/bills/api/client.ts`: client factory and DTO mapping.

## Design

- **Pattern:** Discriminated union (`payload.type`, exhaustive `switch`) + facade over `request()`.

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/model/types.ts` (new), `web/src/features/inbox/api/client.ts` (new), `web/src/features/inbox/api/client.test.ts` (new).

```ts
export type ItemPayload =
  | { readonly type: 'task'; readonly title: string; readonly size?: TaskSize; readonly energy?: Energy; readonly context?: TaskContext;
      readonly doDate?: DateKey | null; readonly dueDate?: DateKey | null; readonly firstStep: string }
  | { readonly type: 'reminder'; readonly title: string; readonly dueDate: DateKey }
  | { readonly type: 'note'; readonly title: string; readonly body: string }
  | { readonly type: 'expense'; readonly description: string; readonly amountCents: number; readonly currency: 'MXN' | 'USD'; readonly spentOn?: DateKey | null }
export interface InboxItem { readonly id: string; readonly dumpId: string; readonly payload: ItemPayload; readonly confidence: number;
  readonly sourceSpan: string; readonly rawText: string; readonly createdAt: string }
export interface DumpResult { readonly items: readonly InboxItem[]; readonly parsed: boolean }

createInboxApi(fetchImpl?, base = '/api') => ({
  postDump: (rawText: string) => Promise<DumpResult>,          // POST /inbox/dumps {rawText, source: 'web'}
  listInbox: () => Promise<readonly InboxItem[]>,              // GET /inbox
})
```

`toInboxItem` drops `status` and `snoozedUntil` (the list only ever holds visible items).

## Steps

1. Types.
2. Client and mapper.
3. Tests.

## Tests

- `postDump sends source web`
- `listInbox maps items`
- `422 on postDump exposes field errors`

## Acceptance criteria

- [ ] Types match BE-089 field for field
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Signed in, browser console:

```js
const { inboxApi } = await import('/src/features/inbox/api/client.ts'); await inboxApi.listInbox()
```

Returns the M4 item.

## Review guide

1. Union matches the backend.
2. Client has only the two functions.

## Out of scope

- Accept/discard → FE-034; snooze → FE-043; accept all → FE-044.

## Notes / log
