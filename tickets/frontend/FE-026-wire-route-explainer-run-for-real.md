# FE-026: Wire the explainer, with the confirmed **Run for real**

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-011: Telegram debugger: explain and replay](../../Epics/EPIC-011-telegram-debugger-explain-replay.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** FE-030, FE-025
- **Can run in parallel with:** FE-024, FE-027 to FE-029
- **Review size:** ~80 lines, 3 files plus tests, ~12 min

## Goal

**Explain** calls the dry-run endpoint and shows the steps. **Run for real…** opens a confirmation that says exactly what will happen, and only then calls the replay endpoint and shows the outcome.

## Why this ticket exists

The one place in the playground where a click creates real records and sends a real reply, so the confirmation step has its own ticket and its own failure modes.

## Read first

- `RouteExplainerPanel` (FE-025), the client (FE-030).
- `web/src/components/ui/`: the dialog primitive (add shadcn's `alert-dialog` if missing).
- BE-076: what a replay does.

## Design

- **Pattern:** Store with two independent actions; a confirmation dialog as the gate for the side effect.
- **Data flow:** **Explain** → `explain()` → steps. **Run for real…** → dialog → confirm → `replay(input, { confirmed: true })` → outcome toast and result line.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/useExplainerStore.ts` (new): `{ value: ComposedUpdate; sample: string | null; errors; explanation; status; replayStatus; lastReplay; setValue; explain(); replay() }`. `replay()` is only called from the dialog's confirm.
- `web/src/features/playground/ExplainTab.tsx` (new): connects store, panel and dialog; loads samples on first show.
- `web/src/features/playground/components/RunForRealDialog.tsx` (new): title 'Run this update for real?'; body: 'This runs the handler as if you sent it from Telegram. It can create records and the bot may reply in your chat.'; buttons **Cancel** (default focus) and **Run for real**. While running: disabled with 'Running…'.
- Tests: `useExplainerStore.test.ts` (new).

After a replay: a result line under the steps ('Processed · core.help · update −1794…'), and a toast. `failed`, `ignored` and `duplicate` are shown plainly, not as crashes. Errors (`409`, network) show in the panel and never leave the dialog stuck open.

## Steps

1. Store with tests.
2. Dialog.
3. Tab wiring.
4. Check with the dev bot.

## Tests

- `test_explain_validates_before_calling`.
- `test_explain_sets_explanation`.
- `test_replay_calls_client_with_confirmed_true`.
- `test_replay_failure_sets_error_and_resets_status`.
- `test_changing_the_form_clears_the_old_explanation`.

## Acceptance criteria

- [ ] **Explain** shows the real explanation and stores nothing server-side
- [ ] **Run for real** runs only after the dialog is confirmed; **Cancel** and Escape do nothing
- [ ] The dialog's default focus is **Cancel**
- [ ] The outcome, including `failed` or `ignored`, is shown
- [ ] Editing the form clears a stale explanation
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Sample `help-command` → **Explain**: three passes, `core.help`.
2. **Run for real…** → **Cancel**: nothing in Telegram. Again → **Run for real**: the help message arrives; the Updates tab shows a row marked playground.

## Review guide

Read the diff in this order, and check:

1. Where is `replay()` called from? Only the dialog's confirm.
2. Dialog: focus on **Cancel**, Escape closes, no double submit.
3. Is a failed replay distinguishable from a network error?

Things that should *not* be in the diff: Bulk replays, saving composed updates.

## Out of scope

- Callback composition → with the callback decoder tool, later.

## Notes / log

The agent adds progress notes, decisions and open questions here.
