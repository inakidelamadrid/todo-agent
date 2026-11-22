# FE-029: Send test message: panel, confirmation and wiring

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-021, FE-022, FE-028
- **Can run in parallel with:** FE-024, FE-026
- **Review size:** ~90 lines, 3 files plus tests, ~12 min

## Goal

From the Test message tab an admin picks a template, fills its fields, confirms, and queues a real message to their own chat; the result says whether it was queued or deferred until a given time.

## Why this ticket exists

A form submit with its own failure modes (hourly limit, quiet hours, Telegram not configured), so it gets its own ticket. It reuses the templates store and the field inputs from the preview.

## Read first

- `useTemplatesStore` (FE-028) and the field inputs in `TemplatePreviewPanel` (FE-027).
- `sendTestMessage` (FE-022) and BE-079's responses.
- The confirmation dialog from FE-026.

## Design

- **Pattern:** Form submit behind a confirmation; a pure function turns the result or error into the message shown.
- **Data flow:** fields → **Send test…** → dialog → `sendTestMessage` → `describeSendResult` → result line and toast.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/sendResult.ts` (new): `describeSendResult(input: { ok: true; result: TestMessageResult } | { ok: false; status: number; detail: string }, now: Date): { tone: 'good' | 'info' | 'bad'; text: string }` (pure):
  - queued → good, 'Queued. It should arrive in a moment.'
  - deferred → info, 'Deferred by quiet hours or pause. Scheduled for 08:00.' (time from `scheduledFor`, America/Mexico_City)
  - `429` → bad, 'Limit reached: 10 test messages per hour.'
  - `409` → bad, 'Telegram is not configured.'
  - other → bad, the detail or a generic line.
- `web/src/features/playground/TestMessageTab.tsx` (new): template select and fields (shared store), **Send test…**, the confirmation ('Send this to your own Telegram chat?', **Cancel** default), the result line.
- Shell usage (changed).
- `sendResult.test.ts` (new).

There is no recipient field anywhere. The button is disabled while sending and while fields are incomplete.

States to polish: loading, empty, error, hover, focus-visible, disabled, phone width, light and dark. Use the tokens and type scale in `DESIGN.md`; this is an internal tool, but not an unstyled one.

## Steps

1. `describeSendResult` with tests.
2. Tab with the dialog.
3. Plug in.
4. Check with the dev bot, by day and during quiet hours.

## Tests

- `test_queued_is_good`.
- `test_deferred_shows_local_time`.
- `test_429_names_the_limit`.
- `test_409_says_not_configured`.
- `test_unknown_error_falls_back_to_detail`.

## Acceptance criteria

- [ ] A confirmed send queues a message and shows queued or deferred with the time
- [ ] **Cancel** sends nothing
- [ ] The limit and not-configured cases show calm, specific messages
- [ ] No recipient can be entered
- [ ] Works at 375 px, with the keyboard, in both themes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Pick `help`, **Send test…**, confirm: 'Queued', and the message arrives (needs the outbound worker, BE-031).
2. After 20:00: the same shows 'Deferred … 08:00'.
3. Send eleven within an hour: the eleventh shows the limit message.

## Review guide

Read the diff in this order, and check:

1. `sendResult.ts`: every documented status handled?
2. Is the send reachable without the dialog? It must not be.

Things that should *not* be in the diff: Free-text messages, choosing a chat, bypassing quiet hours.

## Out of scope

- Callback decoder, policy explainer, session peek, health → later tools, not ticketed.

## Notes / log

The agent adds progress notes, decisions and open questions here.
