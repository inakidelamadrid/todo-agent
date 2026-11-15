# FE-008: Background worker status line in the settings sheet

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [F-6 Scheduler & notifications](../../Epics/README.md#f-6-tickets)
- **Assigned agent / harness / model:**
- **Depends on:** BE-056, FE-007
- **Can run in parallel with:** none
- **Review size:** ~60 lines, 4 files, ~8 min

## Goal

The notification settings sheet shows whether the background worker is running.

## Why this ticket exists

If the worker is down, reminders silently stop. One quiet line next to the Telegram status makes that visible where you already look.

## Read first

- `web/src/features/telegram/` (FE-006, FE-007): the same client, store and `describe…` pattern, to be copied in miniature.
- `DESIGN.md`.

## Design

- **Pattern:** Presentational line over a pure describe function; typed client; narrow store slice.
- **Data flow:** sheet opens → `jobsApi.status()` → `describeJobs(status)` → one status line.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/jobs/model/status.ts` (new) and test: `JobsStatus` type (matching BE-056) and `describeJobs`.
- `web/src/features/jobs/api/client.ts` (new) and test: `createJobsApi().status()`.
- `web/src/features/jobs/components/JobsStatusLine.tsx` (new).
- `web/src/features/notifications/components/NotificationSettingsSheet.tsx` (changed): render it under the Telegram card; load on open.

**`describeJobs(status)`**

| Condition | Tone | Text |
|---|---|---|
| `heartbeat === 'never'` | muted | Reminders aren't running yet |
| `heartbeat === 'stale'` | attention | Reminders are paused: the worker stopped |
| `failures24h > 0` | attention | N background jobs failed today |
| otherwise | ok | Reminders are running |

Same dot + text idiom and tokens as the Telegram card. States: loading (skeleton line), error (muted `Status unavailable`), ready. Its load is independent of the other two in the sheet. The fetch state is local to the sheet (`useState`); a store is not needed for one read-only line.

## Steps

1. Type and `describeJobs` with tests.
2. Client function.
3. The line component.
4. Place it in the sheet.

## Tests

- One test per table row.
- `status calls GET /jobs/status`.

## Acceptance criteria

- [ ] The line reflects the real worker state
- [ ] A failure to load it does not affect the form or the Telegram card
- [ ] No new colour tokens
- [ ] Checked in the browser at desktop and mobile widths
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With the worker running, open Notifications: `Reminders are running`. Stop `make worker-dev`, wait three minutes, reopen: the attention line.

## Review guide

Read the diff in this order, and check:

1. The table against `describeJobs`.
2. Wording.
3. Independence of the three loads in the sheet.

Things that should *not* be in the diff: controls to start or stop the worker.

## Out of scope

- Nothing further planned.

## Notes / log

The agent adds progress notes, decisions and open questions here.
