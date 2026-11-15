# FE-003: Notification settings: types, validation and API client

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §9 Frontend
- **Assigned agent / harness / model:**
- **Depends on:** FE-002, BE-027
- **Can run in parallel with:** none
- **Review size:** ~110 lines, 4 files, ~12 min

## Goal

The frontend has typed notification settings, a pure validator for the form, and client functions for `GET` and `PATCH /settings/notifications`.

## Why this ticket exists

Model and client come before any component, as in the bills feature, so the form in FE-004 is pure presentation over already-tested logic.

## Read first

- `web/src/features/bills/model/types.ts` and `api/client.ts`.
- BE-027: the response shape and the validation table. The frontend rules must match it exactly.
- `CLAUDE.md`: a shared model changes on both sides together.

## Design

- **Pattern:** Typed client functions over the shared request helper; parse at the boundary with a mapping function.
- **Data flow:** `notificationsApi.get()` → DTO → `toSettings` → `NotificationSettings`; form draft → `validateSettings` → `FieldErrors`.

## Packages

None new. Standard library and what is already installed.

Hand-written instead of a package: the validator, five short rules. `zod` (4.6.7, MIT) was considered for parsing the response; with one small object and the server already validating, it does not yet earn a new dependency. Revisit when a third feature needs response parsing.

## Details

**Files**

- `web/src/features/notifications/model/types.ts` (new).
- `web/src/features/notifications/model/validate.ts` (new) and `validate.test.ts`.
- `web/src/features/notifications/api/client.ts` (new) and `client.test.ts`.

**Types** (all `readonly`)

```ts
export type TimeOfDay = `${number}${number}:${number}${number}`   // "20:00"

export interface NotificationSettings {
  readonly quietStart: TimeOfDay
  readonly quietEnd: TimeOfDay
  readonly timezone: string
  readonly pausedUntil: string | null          // ISO 8601 UTC
  readonly urgentCategories: readonly string[]
  readonly caps: Readonly<Record<string, number>>
  readonly groupingWindowMinutes: number
}
export type NotificationSettingsPatch = Partial<NotificationSettings>
```

**Pure functions**

- `validateSettings(draft: NotificationSettings): FieldErrors`: `quietStart` / `quietEnd` match `HH:MM` 24-hour; `groupingWindowMinutes` is an integer 0–120; cap values are integers 0–50; `timezone` is non-empty. Returns `{}` when valid. Messages are short and calm, e.g. `Use a time like 20:00`.
- `isPaused(settings, now: Date): boolean`.
- `diffSettings(saved, draft): NotificationSettingsPatch`: only the fields that changed, so the PATCH is minimal.

**Client**

`createNotificationsApi(fetchImpl?, base?)` → `{ get(): Promise<NotificationSettings>, patch(p): Promise<NotificationSettings> }`, built on `createRequest` from `lib/api.ts`. Export `notificationsApi`.

## Steps

1. Types.
2. `validateSettings`, `isPaused`, `diffSettings` with tests.
3. The client with a fake `fetch`, as `client.test.ts` does for bills.

## Tests

- `validateSettings accepts the server defaults`
- `validateSettings rejects 24:00, 8:00 and empty times`
- `validateSettings rejects a grouping window of 121 and a cap of 51`
- `isPaused is true only before pausedUntil`
- `diffSettings returns only changed fields` and `{}` when nothing changed
- `get calls GET /settings/notifications`
- `patch sends only the given fields`
- `a 422 becomes ApiError with field errors`

## Acceptance criteria

- [ ] Field names and limits match BE-027 exactly
- [ ] All three model functions are pure
- [ ] No component or store in this ticket
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make web-test
```

## Review guide

Read the diff in this order, and check:

1. `types.ts` against BE-027's JSON example.
2. `validateSettings` against BE-027's validation table.
3. `diffSettings`: an unchanged form sends nothing.

Things that should *not* be in the diff: React components, Zustand, styling.

## Out of scope

- The form → FE-004.
- Loading and saving → FE-005.

## Notes / log

The agent adds progress notes, decisions and open questions here.
