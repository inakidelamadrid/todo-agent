# FE-029: Send test message: panel, confirmation and wiring

- **Status:** done
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** FE-021, FE-022, FE-028
- **Can run in parallel with:** FE-024
- **Review size:** ~90 lines, 3 files plus tests, ~12 min

## Goal

From the Test message tab an admin picks a template, fills its fields, confirms, and a real message is sent to their own chat right away; the result says it was sent, or why not.

## Why this ticket exists

A form submit with its own failure modes (hourly limit, Telegram not configured, Telegram refused), so it gets its own ticket. Re-scoped on 2026-11-22: BE-079 sends immediately (no queue, no quiet hours). It reuses the templates store and the field inputs from the preview.

## Read first

- `useTemplatesStore` (FE-028) and the field inputs in `TemplatePreviewPanel` (FE-027).
- `sendTestMessage` (FE-022) and BE-079's responses.
- shadcn/ui `AlertDialog` for the confirmation (FE-026, now in EPIC-011, can reuse it later).

## Design

- **Pattern:** Form submit behind a confirmation; a pure function turns the result or error into the message shown.
- **Data flow:** fields → **Send test…** → dialog → `sendTestMessage` → `describeSendResult` → result line and toast.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/sendResult.ts` (new): `describeSendResult(input: { ok: true; result: TestMessageResult } | { ok: false; status: number; detail: string }): { tone: 'good' | 'bad'; text: string }` (pure):
  - sent → good, 'Sent. Check your Telegram chat.'
  - `429` → bad, 'Limit reached: 10 test messages per hour.'
  - `409` → bad, 'Telegram is not configured.'
  - `502` → bad, 'Telegram refused the message. Try again in a minute.'
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
4. Check with the dev bot.

## Tests

- `test_sent_is_good`.
- `test_429_names_the_limit`.
- `test_502_says_telegram_refused`.
- `test_409_says_not_configured`.
- `test_unknown_error_falls_back_to_detail`.

## Acceptance criteria

- [ ] A confirmed send delivers a message and says so
- [ ] **Cancel** sends nothing
- [ ] The limit and not-configured cases show calm, specific messages
- [ ] No recipient can be entered
- [ ] Works at 375 px, with the keyboard, in both themes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Pick `help`, **Send test…**, confirm: 'Sent', and the message arrives in your chat.
2. Send eleven within an hour: the eleventh shows the limit message.

## Review guide

Read the diff in this order, and check:

1. `sendResult.ts`: every documented status handled?
2. Is the send reachable without the dialog? It must not be.

Things that should *not* be in the diff: Free-text messages, choosing a chat.

## Out of scope

- Callback decoder, policy explainer, session peek, health → later tools, not ticketed.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- FE-026's dialog didn't exist yet: added `components/ui/alert-dialog.tsx` by hand on Base UI's AlertDialog (the shadcn CLI wanted to overwrite `button.tsx`; declined).
- `sendResult.ts`: `describeSendResult` handles sent / 429 / 409 / 502 / other (re-done after BE-079 moved to immediate send; the queued/deferred version is gone).
- `TestMessageTab.tsx`: shares template and fields with the Templates tab; send state stays local; **Cancel** has initial focus; a success toast as well as the result line.
- Checked in Chrome with a fake API: dialog, Cancel sends nothing, result + toast, dark mode, 340 px. Real delivery: BE-079 is merged; check with the dev bot (runbook step 6).
