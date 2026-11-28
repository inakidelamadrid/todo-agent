# FE-038: Inbox item card (presentational)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5, §5.3, §6 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-033, FE-040
- **Can run in parallel with:** FE-036, FE-037
- **Review size:** ~140 lines, 4 files, ~12 min

## Goal

`<InboxItemCard>` shows one parsed item: its type, what the AI understood, how confident it is, and the words you originally used. Action buttons appear only when their handlers are passed.

## Why this ticket exists

The card is where triage happens, so it has to be readable in a glance and never hide the original text (the epic's over-parsing mitigation). In M5 it is shown read-only; M6/M7 pass handlers to light up the buttons.

## Read first

- `DESIGN.md`: Cards, Buttons, Status tags (icon + coloured text, never a filled badge), The Aligned Figures Rule.
- `web/src/features/inbox/model/types.ts` (FE-033).

## Design

- **Pattern:** Presentational component; per-type rendering via a `Record<type, render>` (Strategy) with an exhaustive `switch` fallback.

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/components/InboxItemCard.tsx` (new), `web/src/features/inbox/model/itemView.ts` + `itemView.test.ts` (new), `web/src/features/inbox/fixtures.ts` (new), `web/src/screens.tsx` (changed: dev-only `dev-inbox`).

```ts
interface InboxItemCardProps {
  readonly item: InboxItem
  readonly today: DateKey
  readonly busy?: boolean
  readonly onAccept?: () => void
  readonly onEdit?: () => void
  readonly onSnooze?: () => void
  readonly onLetGo?: () => void
}
```

- **Header:** type label `TASK` / `REMINDER` / `NOTE` / `EXPENSE` (condensed, uppercase, muted) + confidence meter at the right: three 6px dots filled by level, with text for screen readers ("High confidence"). Levels: ≥0.8 high, ≥0.5 medium, else low. Low is muted, never red.
- **Body:** title (Barlow 600, 1rem). Fields as small muted chips: size label, energy, context icon, date via `dateLabel`; expense shows `$600.00 MXN` style amount, tabular, currency code as a label.
- **Original words:** "You said: “call dentist next week”" in muted italic; a **Show full dump** text button expands `rawText` when it differs from the span.
- **Actions** (only those with handlers): **Accept** outline (`Check`), **Edit** ghost, **Snooze** ghost (`Clock`), **Let go** ghost. Accept is disabled for `note` and `expense` with the hint "Notes and expenses can be accepted in a later update." (assumption in the outline).
- **Busy:** 60% opacity, buttons disabled.
- **Phone:** actions wrap to a full-width row of 44px targets.

`itemView(item, today)` (pure) returns header label, confidence level + text, title, chips, span text, `showFullDump`, `canAccept`.

## Steps

1. Fixtures: each type, each confidence level, a long dump, an invented-span item (empty span).
2. `itemView` + tests.
3. Card and dev screen.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen.

- `confidence levels at 0.8 and 0.5 boundaries`
- `note and expense cannot be accepted`
- `expense amount formats cents with currency`
- `full dump toggle only when raw text differs from span`

## Acceptance criteria

- [ ] All fixtures look right on `#dev-inbox` in dark and light
- [ ] No red for low confidence; no filled badges
- [ ] Buttons render only for passed handlers
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make web-dev` → `#dev-inbox`: scan every card; tab through the buttons; 375px.

## Review guide

1. `itemView`: all decisions here, not in JSX.
2. Colours: low confidence muted.

## Out of scope

- The list and its states → FE-039.

## Notes / log
