# EPIC-005: Scheduled weekly reset (15 minutes, guided)

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:** F-1 User login, F-5 AI summaries, F-6 Scheduler & notifications, F-7 Telegram channel
- **Reads from:**
  - EPIC-003 (inbox, tasks, focus sessions);
  - EPIC-004 (radar);
  - Bills and EPIC-002 (money snapshot);
  - EPIC-001 (child support status).

> **Design principle (ADHD):** a reset only works if it **starts by itself, is short, and has an end**. It's scheduled, guided step by step, capped at about 15 minutes, and finished with a clear "done for the week".

## 1. Summary

Every week, at a time I choose (default: Sunday 18:00), Telegram invites me to my **Weekly reset**. One tap opens a guided, **5-step, ~15-minute** flow in the web app, also usable on mobile:

1. **Wins:** what got done.
2. **Clear the inbox.**
3. **Look ahead:** radar for the next 7 days.
4. **Pick the big 3** for the week.
5. **Money snapshot.**

At the end, AI writes a **5-line summary** that is saved and sent to Telegram. If I skip a week, the next reset adapts and doesn't pile up.

## 2. Goals

- A reliable weekly anchor that happens without me remembering it.
- Leave the reset with: an empty inbox, the next 7 days visible, 3 clear priorities, and a money picture.
- Finish in about 15 minutes, with a visible step counter and per-step time hints.
- Build self-trust by highlighting what went right, not only what's left.

## 3. Non-goals (for this epic)

- Daily planning (handled by "What now?" in EPIC-003).
- Journaling or therapy content (possible future: mood trends, if a mood epic exists).
- Long-term goal setting (quarterly OKRs); maybe later.

## 4. User stories

1. On Sunday at 18:00, Telegram says: "Weekly reset · 15 min · ready when you are", with **Start**, **In 1 hour** and **Skip this week** buttons.
2. I tap Start, and the reset opens at step 1 with a progress bar (1/5) and a soft timer.
3. **Step 1, Wins (~2 min):**
   - I see what I finished: tasks done, bills paid, focus minutes, child support signed.
   - I can add a win by hand.
   - AI highlights 1–2 notable ones.
4. **Step 2, Clear the inbox (~4 min):**
   - the EPIC-003 triage inline, with Accept all;
   - stale snoozed items and tasks untouched for over 3 weeks are suggested for **Let go** or reschedule.
5. **Step 3, Look ahead (~3 min):**
   - the EPIC-004 radar for the next 7 days;
   - I confirm, snooze or act on items;
   - AI flags collisions, e.g. "3 deadlines on Thursday + child support due".
6. **Step 4, Big 3 (~4 min):**
   - AI suggests 3 priorities for the week from deadlines, importance and what slipped;
   - I swap, edit and assign a day to each;
   - they get a "Big 3" badge and are favoured by What now?.
7. **Step 5, Money snapshot (~2 min):**
   - this month so far: bills paid vs remaining (per currency), top expense categories (EPIC-002), and child support status;
   - one optional observation, e.g. "Dining is up 40% vs your monthly average".
8. **Finish:**
   - a 5-line AI summary;
   - a calm "Done for the week" screen;
   - the summary is saved to my reset history and sent to Telegram.
9. If I skip a week, the next reset shows **two weeks of wins** but **doesn't** duplicate the work: the inbox and radar are always current.
10. I can pause midway and continue later. Progress is saved per step.

## 5. Functional requirements

### 5.1 Scheduling (F-6)
- Configurable day and time (default Sunday 18:00, America/Mexico_City).
- **Telegram invite:** Start (deep link), Snooze (+1h / +3h / tomorrow), Skip this week.
- One gentle follow-up if it hasn't started within 3 hours, only if I chose that. Quiet hours apply.
- **Never more than one reset open at a time.** A new week's reset replaces an unfinished one, carrying over unfinished steps.

### 5.2 Guided flow
- Five steps in a fixed order. Each step has a time hint and can be skipped ("Skip step" is always visible).
- Per-step progress and state are saved server-side, so it resumes on any device.
- **Soft timer:** shows elapsed time against the 15-minute target. There's no hard stop; past 20 minutes it suggests: "Wrap up? You can finish the rest next week."

### 5.3 Step data
- **Wins:**
  - tasks completed;
  - focus minutes and sessions;
  - bills paid (count and per-currency totals);
  - child support status (paid/signed);
  - manual wins (free text).
- **Inbox:** the EPIC-003 inbox API, plus a "stale" query (snoozed over 14 days, active tasks untouched over 21 days).
- **Look ahead:** the EPIC-004 radar (7 days) plus collision detection (≥3 items on the same day).
- **Big 3:**
  - AI ranking (F-5) over candidate tasks;
  - the user's final choice is stored as `WeeklyFocus` with an optional day per item;
  - What now? (EPIC-003) adds a boost for Big 3 tasks.
- **Money:**
  - bills (per currency, paid vs remaining for the month);
  - expenses by category (EPIC-002, month to date vs the 3-month average);
  - support status (EPIC-001).
  - Sources that don't exist yet are hidden, not shown as empty.

### 5.4 Summary
- F-5 generates **5 lines max** from structured step results only:
  - wins;
  - inbox cleared (n);
  - week ahead (key dates);
  - Big 3;
  - one money note.
- The summary is stored in `WeeklyReset.summary`, with history browsable by week.
- The Telegram message holds the summary text and a link. Amounts appear only if allowed (same setting as EPIC-004).

## 6. UX notes

- **Design:** Midnight Transit. The reset is a **5-station line**; the current station is lit, and completed ones are filled.
  - One step per screen.
  - Big readable type and generous spacing.
  - The primary action is always bottom-right; on mobile it's a sticky bottom bar.
- **Tone:** warm and brief.
  - "Here's what you got done."
  - "Let's clear the inbox, 4 minutes."
  - No guilt words.
- **End screen:** a short, quiet success moment (one authored motion, reduced-motion safe) and "See you next week".
- **History:** a list of past weeks with their summaries; tapping one opens its read-only recap.

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `ResetSettings` | weekday, time, timezone, followUp (bool), includeAmountsInTelegram (bool) |
| `WeeklyReset` | id, weekStart (`YYYY-MM-DD`), status (`scheduled`/`in-progress`/`done`/`skipped`), currentStep, startedAt?, finishedAt?, durationSeconds?, summary? |
| `ResetStepResult` | resetId, step (`wins`/`inbox`/`ahead`/`big3`/`money`), data (json snapshot), completedAt?, skipped (bool) |
| `WeeklyFocus` | resetId, taskId, rank (1–3), plannedDay? |
| `ManualWin` | resetId, text |

## 8. API (draft)

- `GET/PATCH /settings/weekly-reset`.
- `POST /weekly-resets/current` creates or resumes this week's reset.
- `GET /weekly-resets/{id}`, then `POST /weekly-resets/{id}/steps/{step}` (save the result) and `POST /weekly-resets/{id}/finish` (generate the summary).
- `GET /weekly-resets?limit=` for history.
- `GET /weekly-resets/{id}/suggestions/big3` (F-5 ranking).

## 9. Security and privacy

- F-1 login is required. Telegram only gets deep links and the summary, honouring the amounts setting.
- AI receives only aggregated step data (counts, titles, totals), never full documents or child support evidence.

## 10. Epic acceptance criteria

- [ ] The invite arrives at the configured time, and Start, Snooze and Skip work. Quiet hours are respected.
- [ ] The 5-step flow completes in about 15 minutes with real data, resumes across devices, and every step is skippable.
- [ ] Inbox zero is reachable within the reset. Stale items are offered for Let go or reschedule.
- [ ] The radar for the next 7 days shows collisions.
- [ ] Big 3 are saved, and What now? favours them that week.
- [ ] The 5-line summary is accurate (only facts from the data), saved to history, and sent to Telegram.
- [ ] A skipped week doesn't create duplicate work, and the next reset covers both weeks' wins.

## 11. Proposed ticket breakdown (draft)

- **Backend:**
  - Reset settings + scheduler invite (F-6).
  - Reset state machine + step results.
  - Wins and stale-items queries.
  - Big 3 suggestions (F-5).
  - Summary generation (F-5).
- **Frontend:**
  - Guided reset flow (5 stations).
  - Steps 1–5 (reusing the inbox and radar components).
  - End screen.
  - History.
  - Settings.
- **Ops:** n8n / Telegram invite, buttons and summary message.

## 12. Risks

- **Skipping the reset repeatedly.** Mitigation: a short, skippable flow, reminders I control, and one clear "Start".
- **Depends on other epics.** Mitigation: steps for missing sources hide themselves; the MVP works with Bills plus EPIC-003.
- **AI summary inaccuracies.** Mitigation: generated from structured snapshots only, with the numbers shown beside the text.

## 13. Open questions (answer in place)

1. Day and time for the reset?
   - Answer:
2. Follow-up reminder if not started: yes or no? After how long?
   - Answer:
3. Should Big 3 have assigned days, or only "this week"?
   - Answer:
4. Money step: which numbers matter most to you?
   - Answer:
5. Include amounts in the Telegram summary?
   - Answer:
6. Anything else you'd add as a step (e.g. a mood check-in, a gratitude line, a co-parenting week check)?
   - Answer:
