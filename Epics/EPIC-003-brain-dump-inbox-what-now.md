# EPIC-003: Brain-dump inbox + "What now?"

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:**
  - F-1 User login;
  - F-2 Scoped API keys;
  - F-5 AI summaries/planning service;
  - F-6 Scheduler & notifications;
  - F-7 Telegram channel (shared with EPIC-002).
- **Related:**
  - EPIC-002, which uses the same bot and n8n, and receives expenses detected in dumps;
  - EPIC-004, the Deadline radar, which reads task due dates;
  - EPIC-005, the Weekly reset, which clears the inbox.

> **Design principle (ADHD):**
> - Capture must cost almost nothing.
> - Deciding is done for me, or with me, never left as an overwhelming list.
> - Nothing shames me for what's undone.

## 1. Summary

Two halves of one loop:

1. **Brain-dump inbox:** I throw anything at the app (a Telegram text, voice note or photo, or a quick web field). AI turns each dump into structured items:
   - tasks, with size, energy, suggested date and first step;
   - notes;
   - expenses, which go to EPIC-002;
   - reminders.

   Everything lands in an **Inbox** to accept, edit or discard in seconds.
2. **"What now?":** one button (web or `/now` in Telegram) returns **one** task to do right now. It's chosen from deadlines, time of day, my current energy, available time and context, and comes with its tiny first step and a focus timer.

## 2. Goals

- Get thoughts out of my head in under 5 seconds, anywhere.
- No lost items: everything is either in the Inbox or processed.
- Turn vague intentions into concrete, startable tasks.
- Remove the "what should I do?" paralysis with a single, explainable suggestion.
- Keep it gentle: no streaks, no red guilt counters, and a "not now" that's always one tap.

## 3. Non-goals (for this epic)

- Team or shared tasks.
- Full calendar sync (Google Calendar import/export comes later).
- Long-term project management (Gantt charts, dependencies).
- Medical or clinical guidance.

## 4. User stories

### Capture
1. I send `call dentist next week, also buy cat food and pay gym 600`. The Inbox gets three items:
   - task "Call dentist", due next week, size S;
   - task "Buy cat food", errand;
   - expense or bill candidate "gym 600", routed to EPIC-002 for confirmation.
2. I send a voice note while walking. It's transcribed and split the same way.
3. I send a photo of a school notice. AI extracts "Field trip permission slip due Nov 20" as a task with a due date.
4. In the web app, a global **Quick add** field (`/` shortcut) does the same.

### Inbox triage
5. I open the Inbox and see each item as AI parsed it, with buttons: **Accept · Edit · Snooze · Discard**. **Accept all** handles high-confidence items in one go.
6. Items left untriaged for over 3 days get a soft Telegram nudge: "5 items waiting in your inbox, 2 minutes to clear?"

### Task shaping
7. Each accepted task has:
   - **size** (XS ≤5 min · S ≤15 · M ≤45 · L ≤2h · XL needs breaking down);
   - **energy** (low · medium · high);
   - **context** (home · computer · phone · errand · anywhere);
   - an optional **due date** or **do date**;
   - a **first step**.
8. For L/XL tasks, I can tap **Break it down**. AI proposes 3–7 tiny steps; I accept or edit them, and they become subtasks.

### "What now?"
9. I tap **What now?** and answer two quick questions, which can be skipped and remember my last answer:
   - energy: low, medium or high;
   - time I have: 5, 15, 30 or 60+ minutes.
10. I get **one** task with a one-line *why*, e.g. "Due tomorrow, fits your 15 min, low energy is OK", plus its first step, with buttons:
    - **Start** opens a focus timer;
    - **Another** gives the next best, at most 3 rerolls before suggesting a break;
    - **Not today** snoozes it to tomorrow without penalty.
11. **Focus timer:**
    - a countdown with the task and its first step visible;
    - an optional Telegram check-in halfway: "Still on it?";
    - at the end: **Done · Need more time · Stuck**. Stuck offers to break it down further.
12. When nothing fits, it says so kindly and offers a 2-minute reset (water, stretch) instead of an empty state.

## 5. Functional requirements

### 5.1 Capture channels
- **Telegram (shared bot, F-7):**
  - plain messages default to the brain dump;
  - `/now` runs What now?;
  - `/inbox` gives the inbox count with a link;
  - `/done` marks the current focus task done;
  - expense-looking messages are routed to the EPIC-002 flow.
- **Web:** the Quick add field, always reachable; it accepts multi-line text.
- **(Later)** Email-forward address, iOS share sheet.

### 5.2 Parsing (n8n + API)
- n8n handles transcription and OCR, then calls `POST /inbox/dumps` with the raw text and its source.
- The API (F-5) splits the dump into **candidate items** under a strict schema:
  - `type`: task, note, expense, reminder;
  - `title`, `dueDate`/`doDate`, `size`, `energy`, `context`;
  - `firstStep`, `confidence`, and the `sourceSpan` they came from.
- Relative dates ("next week", "el viernes") resolve in America/Mexico_City.
- Expense candidates are **not** saved as expenses until confirmed; they link to the EPIC-002 confirm flow.
- The raw dump is kept, so I can always see what I originally said.

### 5.3 Inbox
- List untriaged items, newest first, with a confidence indicator.
- **Bulk actions:** accept all above the threshold, discard.
- **Snooze:** later today, tomorrow, next week, or a custom date.
- The **Inbox zero** state is calm and celebratory, without streak language.

### 5.4 Tasks
- **Statuses:** `inbox` → `active` → `done`, plus `snoozed` (until a date) and `dropped` (consciously let go; it isn't failure).
- **Fields** are as in §7. Subtasks are allowed one level deep.
- **Recurrence:** daily, weekly, monthly, or custom rule. Recurring tasks never pile up: a missed occurrence becomes the next one, without stacking duplicates.
- **Do date vs due date:**
  - the do date is when I plan to work on it;
  - the due date is a hard deadline that feeds EPIC-004.

### 5.5 "What now?" engine
- **Candidates:** active tasks that aren't snoozed, whose do date ≤ today or which have no do date, filtered by `size` ≤ available time and by `context`.
- **Score (transparent, rule-based first; AI only writes the *why*):**
  - urgency (due date proximity, overdue weight);
  - fit (energy match, size fit);
  - age (how long it's waited);
  - momentum (subtasks of something already started);
  - a penalty for being shown and skipped recently.
- Return **one** task plus up to 2 alternates (for rerolls). The scoring factors are recorded so the choice can be explained.
- **Time-of-day defaults:** e.g. high-energy tasks in the morning. These are learned later from completion times (optional, in a later phase).

### 5.6 Focus sessions
- Session = task, planned minutes, start and end, outcome (`done` · `more-time` · `stuck` · `abandoned`).
- Optional Telegram check-in at 50% and at the end. Quiet hours are respected.
- Sessions feed the Weekly reset (EPIC-005) stats: time focused, tasks finished.

### 5.7 Notifications (F-6)
- Inbox nudge after N days (default 3), at most 1 per day.
- Optional morning message: "Your top 3 for today" plus a What now? button.
- **Quiet hours** (default 22:00–08:00) and a global **pause** ("I need a break for 3 days").

## 6. UX notes

- **Design:** Midnight Transit (`DESIGN.md`).
  - The day is a line, and tasks are stations on it.
  - "Now" is the porcelain TODAY tick, and the What now? choice is the highlighted next station.
- **What now? screen:**
  - one large card;
  - the task title in display type;
  - the first step prominent;
  - the *why* in muted text;
  - three big buttons.
  - No list visible behind it: deliberately minimal to lower overwhelm.
- **Language:** kind and neutral.
  - "Not today" instead of "Skip".
  - "Let go" instead of "Delete".
  - Never "overdue!!!"; say "past its date" in calm colour.
- **Accessibility:** keyboard-first (`/` Quick add, `n` What now), reduced-motion support, large touch targets.

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `Dump` | id, rawText, source (`telegram-text`/`telegram-voice`/`telegram-photo`/`web`), sourceRef, receivedAt, fileId? |
| `InboxItem` | id, dumpId, type (`task`/`note`/`expense`/`reminder`), payload (parsed fields), confidence, status (`new`/`accepted`/`discarded`/`snoozed`), snoozedUntil? |
| `Task` | id, title, notes, status, size, energy, context, doDate?, dueDate?, firstStep, parentId?, recurrenceRule?, createdFrom (inboxItemId?), completedAt?, droppedAt? |
| `Note` | id, title, body, tags[], createdFrom? |
| `FocusSession` | id, taskId, plannedMinutes, startedAt, endedAt?, outcome |
| `Suggestion` | id, taskId, requestedAt, energy, availableMinutes, scoreFactors (json), action (`started`/`rerolled`/`not-today`) |

## 8. API (draft)

- `POST /inbox/dumps` (scoped key `inbox:write` for n8n) → parsed `InboxItem[]`.
- `GET /inbox`, then `POST /inbox/{id}/accept | discard | snooze`, plus `POST /inbox/accept-all?minConfidence=`.
- `GET/POST/PATCH/DELETE /tasks`, with `POST /tasks/{id}/breakdown` (AI proposes subtasks) and `POST /tasks/{id}/complete`.
- `POST /now` with `{energy, availableMinutes, context?}` → `{task, why, alternates[]}`.
- `POST /focus-sessions`, `PATCH /focus-sessions/{id}`.

## 9. Security and privacy

- Tasks and notes can be very personal; F-1 login is required.
- n8n's key is scoped to `inbox:write` + `tasks:read` (for `/now`), never admin.
- AI calls send only the dump text and the minimal task fields, never other records.
- Raw voice and photos are kept only if I opt in (the default is to discard them after parsing).

## 10. Epic acceptance criteria

- [ ] A mixed Telegram dump becomes correctly split Inbox items in ≤10 s. Expense parts route to EPIC-002's confirm flow.
- [ ] Inbox triage of 10 items takes under 1 minute with Accept all and per-item edits.
- [ ] What now? returns one task with a correct, readable *why* in under 1 s (rules), and rerolls avoid recent skips.
- [ ] Break it down produces 3–7 concrete first steps for an L/XL task.
- [ ] Focus sessions record outcomes, and Stuck leads to a breakdown.
- [ ] Quiet hours and pause are respected by every notification.
- [ ] No guilt mechanics: no streaks, no red counters, and "past its date" is shown calmly.

## 11. Proposed ticket breakdown (draft)

- **Backend:**
  - F-7 Telegram channel routing (dump vs expense vs commands).
  - Dumps + inbox API.
  - AI split/parse (F-5).
  - Tasks API (recurrence, subtasks).
  - What now? scoring engine + `/now`.
  - Focus sessions.
  - Nudges (F-6).
- **Frontend:**
  - Quick add.
  - Inbox triage.
  - Task list/detail with breakdown.
  - What now? screen.
  - Focus timer.
  - Settings (quiet hours, pause, energy defaults).
- **Ops:** n8n branches for `/now`, `/inbox`, `/done`.

## 12. Risks

- **Over-parsing** (one thought split wrongly). Mitigation: Inbox review, confidence thresholds, original text visible.
- **Suggestion distrust.** Mitigation: a transparent *why*, deterministic rules first, easy reroll.
- **Notification fatigue.** Mitigation: strict caps, quiet hours, a pause button.
- **Inbox becoming another overwhelming list.** Mitigation: nudges, Accept all, auto-snooze of stale items in the Weekly reset.

## 13. Open questions (answer in place)

1. Which contexts matter to you (home, computer, phone, errand, car, office)?
   - Answer:
2. Should What now? always ask for energy and time, or infer them (time of day, last answer)?
   - Answer:
3. Default focus session lengths (e.g. 10/25/45 min)? Should Telegram check-in during focus be on or off?
   - Answer:
4. Morning "top 3" message: yes or no? At what time?
   - Answer:
5. Quiet hours?
   - Answer:
6. Keep raw voice notes and photos, or discard them after parsing?
   - Answer:
7. Spanish, English or both for the parsing and bot replies?
   - Answer:
8. Do you want Google Calendar visibility (read-only free/busy) to improve "time available"?
   - Answer:
