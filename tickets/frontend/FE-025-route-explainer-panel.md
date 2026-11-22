# FE-025: Route explainer panel: composer form and step list (presentational)

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:**
- **Depends on:** FE-020
- **Can run in parallel with:** FE-021 to FE-024, FE-027
- **Review size:** ~130 lines, 3 files plus tests, ~15 min

## Goal

A panel lets you pick a sample or compose an update, and shows an explanation as an ordered list of steps with the final route, all from props.

## Why this ticket exists

The centrepiece of the playground, so it gets a ticket for its looks and states alone. It is at the top of the size limit; if it grows, split the composer form from the step list.

## Read first

- `web/src/features/bills/components/BillFormSheet.tsx`: form fields, inline errors, disabled submit.
- `DESIGN.md`: Inputs / Fields, Buttons, Status tags, and the network-map idiom (stations on a line) for the step list.
- `ComposedUpdate`, `RouteExplanation`, `validateComposed` in FE-022's ticket.

## Design

- **Pattern:** Two presentational components (`UpdateComposer`, `ExplanationSteps`) in one panel; validation is a pure function passed in.
- **Data flow:** props `{ samples, value, errors, explanation, status, onChange, onExplain, onRunForReal }` → form and steps.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/components/UpdateComposer.tsx` (new): sample select; kind select (text, command, photo, document, voice); a text area for text and command; a caption field for photo and document; inline field errors; **Explain** (primary) and **Run for real…** (secondary, visually quieter, with the ellipsis because it opens a confirmation).
- `web/src/features/playground/components/ExplanationSteps.tsx` (new): the steps as stations on a vertical line: `pass` (filled, accent), `stop` (filled, warning tone, the line ends here), `skipped` (hollow, muted). Each shows its name and detail. Below, the final route as `kind → target` in monospace, or 'Stopped before routing'.
- `web/src/features/playground/components/RouteExplainerPanel.tsx` (new): lays out both, plus the result area states.
- `web/src/features/playground/explainView.ts` (new) with tests: `stepTone(verdict)`, `routeLabel(finalRoute)` (pure).

**States:** idle ('Compose an update or pick a sample, then Explain'), loading, error, result; form invalid (submit disabled, errors shown); `409` hint ('Set TELEGRAM_ALLOWED_USER_ID' as text, no value). Phone width: form above, steps below.

States to polish: loading, empty, error, hover, focus-visible, disabled, phone width, light and dark. Use the tokens and type scale in `DESIGN.md`; this is an internal tool, but not an unstyled one.

## Steps

1. Pure view helpers with tests.
2. `ExplanationSteps` with fixtures for pass, stop and skipped.
3. `UpdateComposer`.
4. The panel; check every state.

## Tests

- `test_step_tone_for_each_verdict`.
- `test_route_label_for_route_and_for_null`.

## Acceptance criteria

- [ ] The composer shows only the fields its kind needs, with inline errors
- [ ] The step list distinguishes pass, stop and skipped without relying on colour alone
- [ ] **Run for real…** is visibly secondary to **Explain**
- [ ] All result states render from props; nothing fetches
- [ ] Works with the keyboard, at 375 px, in both themes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Explain tab with fixtures: a three-pass explanation, a stopped one, and each result state. Check 375 px and dark mode.
2. Tab through the form: order is sample, kind, text, buttons.

## Review guide

Read the diff in this order, and check:

1. Are verdicts readable without colour (icon or text)?
2. Is any logic beyond display in the components?
3. Did the ticket stay within size? If not, was it split?

Things that should *not* be in the diff: API calls, the confirmation dialog, a store.

## Out of scope

- Wiring and the confirmation → FE-026.

## Notes / log

The agent adds progress notes, decisions and open questions here.
