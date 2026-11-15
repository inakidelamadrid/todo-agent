# FE-004: Notification settings form (presentational, all states)

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §9 Frontend
- **Assigned agent / harness / model:**
- **Depends on:** FE-003
- **Can run in parallel with:** none
- **Review size:** ~150 lines, 2 files, ~15 min

## Goal

A `NotificationSettingsForm` component renders quiet hours, pause and the grouping window from props, in every state, with no data fetching.

## Why this ticket exists

Building the form against fixture props lets the design and every state be reviewed in isolation: there is no store or network in the diff to distract from how it looks and behaves.

## Read first

- `DESIGN.md`: Midnight Transit tokens, the `label-caps` style, the rail status idiom.
- `web/src/features/bills/components/BillFormSheet.tsx`: the house form pattern (labels, inline errors, sheet layout).
- `web/src/features/bills/components/LoadStates.tsx`: loading and error idioms.
- Use the `impeccable` skill for the visual pass, as the frontend README requires.

## Design

- **Pattern:** Presentational component: props in, callbacks out, no store access.
- **Data flow:** props `{ settings, status, errors, now, onChange, onSave, onPause, onResume }` → markup.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/notifications/components/NotificationSettingsForm.tsx` (new).
- `web/src/features/notifications/components/NotificationSettingsForm.test.tsx` (new), only if a component test set-up already exists; otherwise verify in the browser and note it in the log. Do not add a testing library in this ticket.

**Props**

```ts
interface Props {
  readonly draft: NotificationSettings
  readonly status: 'loading' | 'ready' | 'saving' | 'error'
  readonly errors: FieldErrors
  readonly dirty: boolean
  readonly now: Date
  readonly onChange: (patch: NotificationSettingsPatch) => void
  readonly onSave: () => void
  readonly onPause: (until: string) => void
  readonly onResume: () => void
  readonly onRetry: () => void
}
```

**Sections**

1. **Quiet hours.** Two time inputs (`<Input type="time">`), labelled "From" and "Until", with the timezone shown as muted text beside them (read-only for now). Helper line: `Messages wait until quiet hours end.`
2. **Pause.** When not paused: three quiet buttons, `1 hour`, `Until tomorrow`, `3 days`. When paused: a status line `Paused until Thu 08:00` and a `Resume` button. Use `isPaused`.
3. **Grouping.** A number input, minutes, 0–120, helper `Messages close together are merged.`
4. **Save** primary button, disabled unless `dirty` and there are no errors.

**States to polish**

- `loading`: skeleton rows matching the final layout (no spinner-only screen).
- `error`: calm inline message with `Retry`; the form is hidden.
- `saving`: Save shows progress and is disabled; inputs stay readable.
- Field error: message under the field, `aria-describedby` wired, `aria-invalid` set.
- Hover, focus-visible and disabled states on every control; all reachable and operable by keyboard in a sensible order.
- Phone width: single column, full-width controls, touch targets at least 44 px.
- Light and dark mode, using existing tokens only. No new colours.

Caps and urgent categories are not shown yet: no feature defines a category until EPIC-004.

## Steps

1. Static layout with fixture props.
2. Wire `onChange` per field.
3. Pause section, both variants.
4. Loading, error and saving states.
5. Keyboard and phone-width pass; impeccable polish.

## Tests

- If component tests exist: `renders the saved times`, `Save is disabled until dirty`, `shows a field error with aria-describedby`, `shows Resume when paused`.
- Otherwise: each state checked in the browser with fixture props and noted in the log.

## Acceptance criteria

- [ ] The component reads no store and makes no request
- [ ] All five states render correctly at desktop and phone widths, in light and dark mode
- [ ] Every control is keyboard-operable with a visible focus ring
- [ ] No new colour tokens or fonts
- [ ] Checked in the browser at desktop and mobile widths
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Temporarily render the component with fixture props (or use the wiring from FE-005 if done together in review): switch `status` through its four values and toggle `pausedUntil`.

## Review guide

Read the diff in this order, and check:

1. The props: nothing store- or API-shaped.
2. Each state against the list above.
3. Copy: calm, no exclamation marks.
4. Tab through it.

Things that should *not* be in the diff: fetching, saving, toasts, the rail entry point.

## Out of scope

- Loading and saving → FE-005.
- Caps and categories UI → when EPIC-004 adds categories.

## Assumptions

- The timezone is displayed but not editable in this first version.

## Notes / log

The agent adds progress notes, decisions and open questions here.
