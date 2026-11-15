# EPIC-004: Deadline radar

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:** F-1 User login, F-6 Scheduler & notifications, F-7 Telegram channel
- **Reads from:**
  - Bills (existing): due dates and payment status;
  - EPIC-001 Child support: obligations and pending signatures;
  - EPIC-003 Tasks with due dates;
  - EPIC-006 Documents vault: expiry dates.

> **Design principle (ADHD):** losing track of time is the problem, not laziness. The radar makes upcoming deadlines **visible early, in one place, without panic**.

## 1. Summary

One merged, time-ordered view of **everything with a date coming up in the next 14 days, plus anything past its date**:
- bills;
- child support payments and signatures;
- task deadlines;
- expiring documents;
- one-off appointments.

Each item shows its type, how far away it is, and the one action that clears it ("Mark paid", "Request signature", "Open task", "Renew"). Telegram sends **staged, capped nudges** (7 / 3 / 1 days, and on the day), and a short daily radar digest is optional.

## 2. Goals

- Never miss a payment, signature, renewal or deadline because it was out of sight.
- One place to look, not five.
- Clear each item from the radar with its own one-tap action.
- Reminders that help without nagging: staged, grouped, capped, quiet-hours aware.

## 3. Non-goals (for this epic)

- Being the source of truth for any item. The radar **reads** from the other features, and actions call those features' APIs.
- A full calendar app.
- Event syncing with external calendars (later: export as ICS).

## 4. User stories

1. I open **Radar** and see the next 14 days on a horizontal line, plus a "Past its date" section first. Each item is a station coloured by type.
2. Each item shows:
   - its title;
   - its type chip (Bill · Child support · Task · Document · Appointment);
   - its date and "in N days";
   - its amount, when it has one;
   - its **primary action**.
3. I tap **Mark paid** on a bill. The radar calls the bills API, and the item disappears with a calm confirmation.
4. I change the window (7 / 14 / 30 days) and filter by type.
5. Telegram sends **"3 things coming up in the next 3 days"**, grouped in one message, with deep links. At most one grouped radar message per day, unless something is due **today**.
6. I add a one-off **appointment** (e.g. "SAT appointment Nov 21 10:00") directly in the radar, or through a brain dump (EPIC-003).
7. I **snooze** an item's reminders ("remind me again in 2 days") without changing the underlying date.
8. Items past their date stay visible in a calm "Past its date" group, with the same one-tap actions. There's no red alarm styling, but they're clearly first.

## 5. Functional requirements

### 5.1 Sources (adapters)

The radar has one adapter per source. Each adapter maps its records into a common `RadarItem`.

| Source | Becomes a radar item when… | Primary action |
|---|---|---|
| Bills | An occurrence in the window is unpaid | Mark paid (opens the amount popover) |
| Child support (EPIC-001) | The month is unpaid or partial, or the acknowledgment is pending more than N days | Record payment · Remind recipient |
| Tasks (EPIC-003) | A task has a `dueDate` in the window and isn't done or dropped | Open · Start focus |
| Documents (EPIC-006) | A document's `expiresAt` is within its own lead time (e.g. passport 6 months) | Open document · Mark renewed |
| Appointments (this epic) | The `startsAt` is in the window | Open · Done |

- New sources plug in as adapters, with no changes to the radar UI.
- Adapters run server-side. `GET /radar` merges them and sorts by date, then by priority.

### 5.2 Window and priority
- Default window: 14 days ahead, plus everything past its date (up to 60 days back).
- **Priority:** past its date → due today → money items → hard deadlines → the rest.
- Documents use **per-type lead times** (passport 180 days, ID or licence 60, insurance 30, all configurable) so renewals surface early enough.

### 5.3 Reminders (F-6)
- **Stages:** 7 days, 3 days, 1 day, and the day itself (configurable per type; e.g. bills 3/1/0, documents 90/30/7).
- **Grouping:** reminders due on the same day merge into **one** Telegram message.
- **Caps:** at most 1 grouped radar message per day, plus 1 "due today" message. Quiet hours and global pause (EPIC-003) apply.
- Per-item reminder snooze, separate from the item's actual date.
- **Optional daily digest** at a set time: "Radar: 2 today, 4 this week" plus a link.

### 5.4 Appointments
- A minimal entity owned by this epic: title, `startsAt`, optional `endsAt`, location, notes, and reminder stages.
- Can be created from a brain dump (EPIC-003 can parse `appointment`).

### 5.5 Actions
- Actions call the owning feature's API: the bills payment PUT, EPIC-001 payment or reminder, EPIC-003 task complete, EPIC-006 document renew.
- After an action, the radar refreshes that item only, with an optimistic update and rollback on failure, as in FE-001.

## 6. UX notes

- **Design:** Midnight Transit.
  - The radar is a **single line** for the next N days, with the TODAY tick at the left.
  - Stations are coloured by type: bill lines keep their ink, and child support, task, document and appointment get new tokens.
  - Below the line sits the grouped list (Past its date · Today · This week · Later).
- **Summary chip in the app rail:** "Radar: 2 today" with a dot, matching the existing rail status idiom.
- **Mobile:** the list comes first; the line becomes a compact horizontal scroller.
- **Language:** "Past its date", never "OVERDUE!"; amounts in tabular figures, per currency.

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `RadarItem` (computed, not stored) | id (`<source>:<sourceId>:<period?>`), source, title, date, daysAway, amountCents?, currency?, status, primaryAction {kind, target} |
| `Appointment` | id, title, startsAt, endsAt?, location?, notes, reminderStages[] |
| `ReminderState` | radarItemId, stage, sentAt, snoozedUntil? |
| `ReminderSettings` | perType {stages[], leadDays}, digestTime?, maxPerDay |

## 8. API (draft)

- `GET /radar?days=14&types=bill,support,task,document,appointment` → `RadarItem[]` with a `past` group.
- `POST /radar/{itemId}/snooze` `{until}` (reminders only).
- `GET/POST/PATCH/DELETE /appointments`.
- `GET/PATCH /settings/reminders`.
- An internal scheduled job (F-6) evaluates reminder stages every 15 minutes, then groups and sends through Telegram.

## 9. Security and privacy

- `/radar` aggregates sensitive sources (child support, documents). F-1 login is required, with no API-key-only access except a scoped read for the Telegram digest (`radar:read`).
- Telegram messages show **titles and dates only** by default. Amounts and document numbers appear only if I enable them.

## 10. Epic acceptance criteria

- [ ] The radar shows unpaid bills, pending child support items, due tasks, expiring documents and appointments in one sorted view, with correct "in N days".
- [ ] Each item's primary action works from the radar and removes or updates the item.
- [ ] Staged Telegram reminders arrive grouped, respect caps, quiet hours and pause, and per-item snooze works.
- [ ] Document lead times surface renewals early (e.g. a passport 6 months before expiry).
- [ ] Past-its-date items are first, calmly styled, and actionable.
- [ ] Adding a new source requires only a new adapter (proven with appointments).

## 11. Proposed ticket breakdown (draft)

- **Backend:**
  - Radar aggregation + bills adapter.
  - Appointments API.
  - Reminder scheduler (F-6) with grouping, caps and quiet hours.
  - Adapters for support, tasks and documents (as those epics land).
  - Reminder settings.
- **Frontend:**
  - Radar view (line + grouped list).
  - Rail chip.
  - Appointment quick add.
  - Reminder settings.
- **Ops:** n8n / Telegram message templates for grouped reminders and the digest.

## 12. Risks

- **Reminder fatigue.** Mitigation: grouping, caps, quiet hours, per-type stages, a pause.
- **Stale data** when a source changes. Mitigation: computed on read, no duplicated state.
- **Sources landing at different times.** Mitigation: the adapter pattern; ship with bills and appointments first.

## 13. Open questions (answer in place)

1. Default window: 7, 14 or 30 days?
   - Answer:
2. Reminder stages per type (bills, child support, tasks, documents, appointments)?
   - Answer:
3. Daily radar digest: yes or no? At what time?
   - Answer:
4. Show amounts in Telegram messages, or titles only?
   - Answer:
5. Which document types, with what lead times (passport, INE, licence, car insurance, health insurance, visa, other)?
   - Answer:
6. Do you want ICS export (subscribe in Google/Apple Calendar)?
   - Answer:
