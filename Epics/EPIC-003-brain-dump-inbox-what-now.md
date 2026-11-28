# EPIC-003: Brain-dump inbox + "What now?"

- **Status:** draft (Phase 1 in tickets; later phases not yet ticketed)
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

## 11. Ticket breakdown

**Phase 1 (core loop)** is ticketed, in 11 milestones that each end with a demo you can run yourself. Map, demos, decisions and assumptions: [outlines/Phase_1_outline_EPIC-003.md](../outlines/Phase_1_outline_EPIC-003.md).

### M1 n8n runs locally

- [BE-109](../tickets/backend/BE-109-n8n-compose-service.md): Self-hosted n8n service in docker-compose. Depends on: none
- [BE-110](../tickets/backend/BE-110-n8n-make-targets.md): Make targets to start, stop and check n8n. Depends on: BE-109
- [BE-111](../tickets/backend/BE-111-n8n-runbook.md): RUNBOOK-n8n-setup.md. Depends on: BE-110

### M2 Tasks through the API

- [BE-080](../tickets/backend/BE-080-task-schemas.md): Task schemas. Depends on: none
- [BE-081](../tickets/backend/BE-081-task-status-rules.md): Task status state machine and size rules. Depends on: BE-080
- [BE-082](../tickets/backend/BE-082-tasks-table-migration.md): tasks table and migration. Depends on: BE-080
- [BE-083](../tickets/backend/BE-083-task-repository-read.md): Task repository: list and get. Depends on: BE-082
- [BE-084](../tickets/backend/BE-084-task-repository-write.md): Task repository: create, update, delete. Depends on: BE-083
- [BE-085](../tickets/backend/BE-085-get-tasks-routes.md): GET /tasks and GET /tasks/{id}. Depends on: BE-084
- [BE-086](../tickets/backend/BE-086-post-tasks-route.md): POST /tasks. Depends on: BE-085
- [BE-087](../tickets/backend/BE-087-patch-delete-task-routes.md): PATCH and DELETE /tasks/{id}. Depends on: BE-086
- [BE-088](../tickets/backend/BE-088-task-status-actions.md): Task status actions: complete, snooze, drop, reopen. Depends on: BE-081, BE-087

### M3 Tasks in the browser

- [FE-040](../tickets/frontend/FE-040-screen-registry.md): Data-driven screen registry (refactor, no behaviour change). Depends on: none
- [FE-031](../tickets/frontend/FE-031-task-types-model.md): Task types and pure model. Depends on: BE-080
- [FE-032](../tickets/frontend/FE-032-tasks-api-client.md): Tasks API client. Depends on: FE-031, BE-088
- [FE-051](../tickets/frontend/FE-051-task-list.md): Task list (presentational). Depends on: FE-031, FE-040
- [FE-052](../tickets/frontend/FE-052-wire-task-list.md): Wire the task list and the Tasks screen. Depends on: FE-032, FE-040, FE-051

### M4 Brain dump through the API

- [BE-089](../tickets/backend/BE-089-inbox-schemas.md): Inbox schemas: dumps and candidate items. Depends on: BE-080
- [BE-090](../tickets/backend/BE-090-dump-parser-port.md): DumpParser port, strict result schema and fake. Depends on: BE-089
- [BE-092](../tickets/backend/BE-092-dumps-inbox-tables.md): dumps and inbox_items tables. Depends on: BE-089
- [BE-093](../tickets/backend/BE-093-parse-mapping-clock.md): Map parser output to inbox drafts, and today in Mexico City. Depends on: BE-090
- [BE-094](../tickets/backend/BE-094-inbox-repository.md): Inbox repository: save a dump, list new items, get one. Depends on: BE-092, BE-093
- [BE-095](../tickets/backend/BE-095-post-inbox-dumps.md): POST /inbox/dumps. Depends on: BE-093, BE-094
- [BE-096](../tickets/backend/BE-096-get-inbox.md): GET /inbox. Depends on: BE-094
- [BE-113](../tickets/backend/BE-113-dev-split-parser.md): Dev-only splitter parser (DUMP_PARSER=dev). Depends on: BE-090, BE-095

### M5 Quick add and Inbox in the browser

- [FE-033](../tickets/frontend/FE-033-inbox-types-client.md): Inbox types and API client (dump, list). Depends on: BE-096
- [FE-035](../tickets/frontend/FE-035-keyboard-shortcut-hook.md): Global keyboard shortcut helper and hook. Depends on: none
- [FE-036](../tickets/frontend/FE-036-quick-add-field.md): Quick add field (presentational). Depends on: FE-040
- [FE-037](../tickets/frontend/FE-037-wire-quick-add.md): Wire Quick add: the / shortcut, POST /inbox/dumps and a toast. Depends on: FE-033, FE-035, FE-036
- [FE-038](../tickets/frontend/FE-038-inbox-item-card.md): Inbox item card (presentational). Depends on: FE-033, FE-040
- [FE-039](../tickets/frontend/FE-039-inbox-list.md): Inbox list with loading, error and inbox-zero states. Depends on: FE-038
- [FE-041](../tickets/frontend/FE-041-wire-inbox-screen.md): Wire the Inbox screen (read-only). Depends on: FE-033, FE-039, FE-040

### M6 Accept and let go

- [BE-097](../tickets/backend/BE-097-task-from-item.md): Turn an inbox item into a task (pure). Depends on: BE-081, BE-089
- [BE-098](../tickets/backend/BE-098-accept-discard-items.md): POST /inbox/{id}/accept and /discard. Depends on: BE-084, BE-096, BE-097
- [FE-034](../tickets/frontend/FE-034-inbox-accept-let-go.md): Accept and Let go in the Inbox. Depends on: FE-033, FE-041, BE-098

### M7 Edit, snooze, accept all

- [BE-099](../tickets/backend/BE-099-snooze-inbox-item.md): Snooze an inbox item. Depends on: BE-093, BE-098
- [BE-100](../tickets/backend/BE-100-accept-all.md): POST /inbox/accept-all. Depends on: BE-098
- [FE-042](../tickets/frontend/FE-042-edit-before-accept.md): Edit an item before accepting. Depends on: FE-034
- [FE-043](../tickets/frontend/FE-043-snooze-popover.md): Snooze an inbox item. Depends on: FE-034, BE-099
- [FE-044](../tickets/frontend/FE-044-accept-all.md): Accept all. Depends on: FE-034, BE-100 (BE-113 for the hand check)

### M8 Real AI splitting (blocked on BE-038, BE-041)

- [BE-091](../tickets/backend/BE-091-n8n-dump-parser-adapter.md): n8n adapter for DumpParser. Depends on: BE-038, BE-041, BE-090, BE-110, BE-113
- [BE-112](../tickets/backend/BE-112-parse-dump-workflow.md): Build and export the parse_dump workflow. Depends on: BE-041, BE-091, BE-111

### M9 What now? through the API

- [BE-101](../tickets/backend/BE-101-now-candidates.md): What now? request and candidate rules. Depends on: BE-081
- [BE-102](../tickets/backend/BE-102-now-scoring.md): What now? scoring and ranking. Depends on: BE-101
- [BE-103](../tickets/backend/BE-103-now-why-line.md): The "why" line for a suggestion. Depends on: BE-102
- [BE-104](../tickets/backend/BE-104-suggestions-table-repository.md): suggestions table and repository. Depends on: BE-082
- [BE-105](../tickets/backend/BE-105-post-now.md): POST /now. Depends on: BE-085, BE-093, BE-103, BE-104
- [BE-106](../tickets/backend/BE-106-now-actions.md): POST /now/{suggestionId}/action. Depends on: BE-088, BE-105

### M10 What now? in the browser

- [FE-045](../tickets/frontend/FE-045-now-types-client.md): What now? types and API client. Depends on: BE-106, FE-032
- [FE-046](../tickets/frontend/FE-046-now-questions.md): Energy and time questions. Depends on: FE-045, FE-040
- [FE-047](../tickets/frontend/FE-047-now-card.md): What now? card and the kind reset. Depends on: FE-045, FE-040
- [FE-048](../tickets/frontend/FE-048-wire-what-now.md): Wire What now?: #now, the n shortcut, rerolls. Depends on: FE-035, FE-040, FE-046, FE-047

### M11 Focus timer

- [BE-107](../tickets/backend/BE-107-focus-sessions-schema-table.md): Focus session schemas and table. Depends on: BE-082
- [BE-108](../tickets/backend/BE-108-focus-sessions-routes.md): POST /focus-sessions and PATCH /focus-sessions/{id}. Depends on: BE-088, BE-107
- [FE-049](../tickets/frontend/FE-049-focus-timer.md): Focus timer (presentational). Depends on: FE-040, FE-031
- [FE-050](../tickets/frontend/FE-050-wire-focus-timer.md): Wire the focus timer to focus sessions. Depends on: BE-108, FE-048, FE-049

### Remaining (later phases, not yet ticketed)

- Telegram capture (plain messages → dumps) plus `/now`, `/inbox`, `/done`, and expense routing to EPIC-002.
- Notes entity (accepting `note` items).
- AI "Break it down" (`POST /tasks/{id}/breakdown`), and recurrence.
- Inbox nudges, the morning top-3 message, the halfway focus check-in (F-6, EPIC-010).
- Settings screen (quiet hours, pause, energy defaults).
- AI-written *why* lines; time-of-day learning.
- n8n Ops branches for `/now`, `/inbox`, `/done`.

## 12. Risks

- **Over-parsing** (one thought split wrongly). Mitigation: Inbox review, confidence thresholds, original text visible.
- **Suggestion distrust.** Mitigation: a transparent *why*, deterministic rules first, easy reroll.
- **Notification fatigue.** Mitigation: strict caps, quiet hours, a pause button.
- **Inbox becoming another overwhelming list.** Mitigation: nudges, Accept all, auto-snooze of stale items in the Weekly reset.

## 13. Open questions (answer in place)

1. Which contexts matter to you (home, computer, phone, errand, car, office)?
   - Answer: home · computer · phone · errand · anywhere.
2. Should What now? always ask for energy and time, or infer them (time of day, last answer)?
   - Answer: Ask both, prefilled with the last answer; both can be skipped.
3. Default focus session lengths (e.g. 10/25/45 min)? Should Telegram check-in during focus be on or off?
   - Answer: 10 / 25 / 45 min (25 preselected). Telegram check-in off by default.
4. Morning "top 3" message: yes or no? At what time?
   - Answer: Deferred to a later phase.
5. Quiet hours?
   - Answer: 22:00–08:00, through the EPIC-010 notification policy.
6. Keep raw voice notes and photos, or discard them after parsing?
   - Answer: Discard after parsing (reuse the BE-045 keep-or-discard prompt).
7. Spanish, English or both for the parsing and bot replies?
   - Answer: Both Spanish and English.
8. Do you want Google Calendar visibility (read-only free/busy) to improve "time available"?
   - Answer: No (non-goal for now).
