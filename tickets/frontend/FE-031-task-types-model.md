# FE-031: Task types and pure model

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4, §6 · Milestone M3 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-080
- **Can run in parallel with:** FE-040
- **Review size:** ~100 lines, 3 files, ~10 min

## Goal

`web/src/features/tasks/model/` mirrors BE-080's Task type and holds the pure display rules: size labels, calm date wording and grouping by do date.

## Why this ticket exists

The Task shape is shared by both sides (CLAUDE.md: change both together). This is the frontend half of BE-080, plus the wording rules the epic insists on ("past its date", never "overdue!!!"), tested before any component uses them.

## Read first

- `web/src/features/bills/model/types.ts` and `schedule.ts`: `readonly` types, `DateKey`, pure helpers.
- `api/app/tasks/schemas.py` (BE-080): field names and enums.

## Design

- **Pattern:** Immutable value objects (`readonly` types) and pure functions.

## Packages

None new (`Intl.DateTimeFormat` for weekday names).

## Details

**Files:** `web/src/features/tasks/model/types.ts` (new), `web/src/features/tasks/model/tasks.ts` (new), `web/src/features/tasks/model/tasks.test.ts` (new).

```ts
export type TaskSize = 'XS' | 'S' | 'M' | 'L' | 'XL'
export type Energy = 'low' | 'medium' | 'high'
export type TaskContext = 'home' | 'computer' | 'phone' | 'errand' | 'anywhere'
export type TaskStatus = 'active' | 'snoozed' | 'done' | 'dropped'
export interface Task { readonly id: string; readonly title: string; readonly notes: string; readonly size: TaskSize;
  readonly energy: Energy; readonly context: TaskContext; readonly doDate: DateKey | null; readonly dueDate: DateKey | null;
  readonly firstStep: string; readonly parentId: string | null; readonly status: TaskStatus; readonly snoozedUntil: DateKey | null }
```

Pure functions:

- `SIZE_LABEL: Record<TaskSize, string>`: `XS · 5 min`, `S · 15 min`, `M · 45 min`, `L · 2 h`, `XL · break it down`.
- `dateLabel(task, today: DateKey): { text: string; tone: 'muted' | 'normal' } | null`: due date first, else do date. Wording: past → `Past its date` (muted, **never** a warning colour); today → `Due today`; tomorrow → `Due tomorrow`; within 6 days → `Due Fri`; else `Due 28 Nov`. Do-date variants say `Planned for …`.
- `groupByDoDate(tasks, today): readonly { key: 'today' | 'upcoming' | 'anytime'; label: string; tasks: readonly Task[] }[]`: `today` = do date ≤ today or due date ≤ today; `upcoming` = later do date; `anytime` = no dates. Empty groups omitted. Within a group: due date, then title.

## Steps

1. Types.
2. Functions.
3. Tests.

## Tests

- `dateLabel says "Past its date" in a muted tone`
- `dateLabel prefers due date over do date`
- `groupByDoDate puts past-due tasks in today`
- `groupByDoDate omits empty groups`
- `SIZE_LABEL covers every size`

## Acceptance criteria

- [ ] Types match BE-080 field for field
- [ ] No wording uses "overdue", "late" or exclamation marks
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
npm --prefix web test -- tasks/model
```

Read the `dateLabel` test table: it is the wording you'll see in the app.

## Review guide

1. `types.ts` against `api/app/tasks/schemas.py`.
2. `dateLabel`: tone for past dates is `muted`.

Things that should *not* be in the diff: components, API calls.

## Out of scope

- API client → FE-032.

## Notes / log
