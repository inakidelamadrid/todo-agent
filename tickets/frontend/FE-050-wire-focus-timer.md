# FE-050: Wire the focus timer to focus sessions

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 11, §5.6 · Milestone M11 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-108, FE-048, FE-049
- **Can run in parallel with:** none (closes Phase 1)
- **Review size:** ~110 lines, 5 files, ~12 min

## Goal

**Start** on the What now? card opens the length picker, starts a focus session, runs the timer, and records the outcome: Done completes the task, Need more time starts another session, Stuck ends calmly.

## Why this ticket exists

The M11 demo and the end of Phase 1's loop: capture → triage → what now → focus → done.

## Read first

- `web/src/features/now/NowScreen.tsx` and `flow.ts` (FE-048).
- `web/src/features/focus/` (FE-049).

## Design

- **Pattern:** Connected component; focus steps added to the What now? reducer (`focusing`, `finished`) so the flow stays in one tested place.

## Packages

None new.

## Details

**Files:** `web/src/features/focus/api/client.ts` + `.test.ts` (new: `startSession(taskId, minutes)`, `endSession(id, outcome)`), `web/src/features/focus/useNow.ts` (new: ticks `Date.now()` every second while mounted), `web/src/features/now/model/flow.ts` + `.test.ts` (changed: `picking-length`, `focusing`), `web/src/features/now/NowScreen.tsx` (changed: replace the placeholder toast).

- Start → length picker (10 · 25 · 45, last choice remembered like FE-046) → `startSession` → timer.
- **Done** → `endSession('done')` → toast "Done." → back to the questions.
- **Need more time** → `endSession('more-time')` → new session with the same length.
- **Stuck** → `endSession('stuck')` → card: "Stuck is useful information. Try only the first step for 5 minutes, or let it go for today." with **5 more minutes** (new 5-minute session) and **Not today** (snooze). The AI breakdown comes in a later phase.
- **Stop** → `endSession('abandoned')` → back to the card, no judgement.
- Reload while focusing → back to the questions (resume is out of scope; the open session stays without an outcome).

## Steps

1. Client + tests.
2. Reducer steps + tests.
3. Screen wiring.

## Tests

- `startSession posts taskId and plannedMinutes`
- `done ends the session and returns to asking`
- `more time starts a new session with the same length`
- `stuck offers five more minutes`

## Acceptance criteria

- [ ] M11 demo: Start → 10 min → Done → task `done` in `#tasks`, session with outcome `done` in the DB
- [ ] Stuck and Stop record their outcomes without guilt language
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`n` → Show me → Start → 10 → let it run a few seconds → I'm done → Done. Check `#tasks` and `select outcome from focus_sessions` in `make db-psql`.

## Review guide

1. All transitions in `flow.ts`.
2. Copy for Stuck and Stop.

## Out of scope

- Resume after reload, Telegram check-in, AI breakdown on Stuck → deferred.

## Notes / log
