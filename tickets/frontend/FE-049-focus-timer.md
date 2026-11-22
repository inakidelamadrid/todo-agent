# FE-049: Focus timer (presentational)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 11, §6 · Milestone M11 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-040, FE-031
- **Can run in parallel with:** everything in M9–M10
- **Review size:** ~150 lines, 4 files, ~14 min

## Goal

`<FocusTimer>` shows a calm countdown with the task and its first step visible, and at the end offers **Done · Need more time · Stuck**. Time maths is pure.

## Why this ticket exists

Timers are easy to get subtly wrong (tab sleeping, drift). Computing the remaining time from `startedAt` and `now`, instead of counting ticks, avoids that, and gets its own tests.

## Read first

- `DESIGN.md`: Network Map (a line filling toward a station is the progress metaphor), Motion, The Aligned Figures Rule.

## Design

- **Pattern:** Presentational component + pure time functions; the clock (`now`) is a prop.

## Packages

None new.

## Details

**Files:** `web/src/features/focus/model/timer.ts` + `.test.ts` (new), `web/src/features/focus/components/FocusTimer.tsx` (new), `web/src/features/focus/components/LengthPicker.tsx` (new: 10 · 25 · 45 chips, 25 preselected), `web/src/screens.tsx` (changed: dev-only `dev-focus` with a 1-minute timer).

```ts
export const remainingMs = (startedAt: number, plannedMinutes: number, now: number): number   // clamped ≥ 0
export const formatClock = (ms: number): string      // "24:59", "0:05"
export const progress = (startedAt, plannedMinutes, now): number   // 0..1
interface FocusTimerProps { readonly task: Task; readonly plannedMinutes: number; readonly startedAt: number; readonly now: number
  readonly onDone: () => void; readonly onMoreTime: () => void; readonly onStuck: () => void; readonly onStop: () => void; readonly busy?: boolean }
```

- **Running:** `FOCUS` label; the clock in Display size, tabular; a horizontal line that fills left to right toward a ringed station; task title and `FIRST STEP` below; a small ghost **Stop** (records `abandoned` in FE-050).
- **Finished** (remaining 0, or the user taps **I'm done** early): three 48px buttons: **Done** primary scarlet, **Need more time** outline, **Stuck** outline.
- The document title shows `24:59 · Focus` while running.
- **Reduced motion:** the line updates once per minute instead of smoothly.
- Accessible: the clock is not announced every second; an `aria-live="polite"` message at 5 minutes left and at the end.

## Steps

1. `timer.ts` + tests.
2. Length picker, timer, dev screen.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen.

- `remainingMs clamps at zero`
- `formatClock pads seconds`
- `progress is 0 at start and 1 at the end`
- `a sleeping tab still shows the right time` (jump `now` forward)

## Acceptance criteria

- [ ] `#dev-focus` 1-minute timer reaches 0:00 and shows the three buttons
- [ ] Reduced motion respected; screen reader isn't spammed
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make web-dev` → `#dev-focus`: watch a minute run down; switch tabs for 30 s and come back: the time is right.

## Review guide

1. Time derived from `startedAt`, never decremented.
2. One scarlet button at the end.

## Out of scope

- API wiring → FE-050. Telegram halfway check-in → deferred.

## Notes / log
