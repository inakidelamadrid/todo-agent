# BE-033: "Working on it…" then edit: service edit and delete

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Response time, §5.3, §8
- **Assigned agent / harness / model:**
- **Depends on:** BE-021, BE-050, BE-051
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~10 min

## Goal

A handler can acknowledge immediately with "Working on it…", hand slow work to a background job, and have the job replace that message with the result.

## Why this ticket exists

Telegram expects the webhook to answer within seconds, and AI calls take longer. The slow part runs as a background job through the `JobQueue` port from F-6.

## Read first

- `api/app/telegram/service.py`.
- `api/app/jobs/queue.py`: `JobQueue.enqueue`, `JobRequest`, `JobContext` (BE-047, BE-050, BE-051).

## Design

- **Pattern:** Command: the handler enqueues a job describing the work; the job finishes by editing the placeholder.
- **Data flow:** handler → `reply(working)` → `SentMessage.message_id` → `ctx.jobs.enqueue(JobRequest(..., payload={chat_id, message_id}))` → job → `service.edit(...)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/service.py` (changed): `async def edit(sender, chat_id, message_id, reply: Reply) -> None`, `async def delete(sender, chat_id, message_id) -> None`.
- `api/app/telegram/handlers.py` (changed): `HandlerContext` gains `reply_now: Callable[[Reply], Awaitable[SentMessage]]` and `jobs: JobQueue` (BE-047).
- `api/tests/test_telegram_working.py` (new).

**Behaviour**

- `edit` renders like `reply` and calls `sender.edit`. An edit to identical text is treated as success (Telegram reports "message is not modified").
- If the job fails permanently, the placeholder is edited to a calm failure template `could_not_finish` = `I couldn't finish that. Nothing was saved.`
- A demonstration handler is **not** added; EPIC-003 is the first real user.

## Steps

1. `edit` and `delete` on the service.
2. Extend the context.
3. Tests with `inline_job_queue` from `api/tests/fakes.py`.

## Tests

- `test_edit_renders_and_calls_sender_edit`
- `test_unmodified_edit_is_success`
- `test_working_then_result_edits_same_message`
- `test_failed_job_edits_to_could_not_finish`

## Acceptance criteria

- [ ] The webhook returns before the slow work runs
- [ ] The user sees one message that changes, not two
- [ ] A failed job never leaves "Working on it…" on screen
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. `service.edit`.
2. The failure path: the placeholder is always replaced.

Things that should *not* be in the diff: any AI call (BE-038 and the feature epics).

## Out of scope

- n8n calls inside jobs → BE-038 and EPIC-003.

## Notes / log

The agent adds progress notes, decisions and open questions here.
