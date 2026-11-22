# FE-046: Energy and time questions

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 9 · Milestone M10 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-045, FE-040
- **Can run in parallel with:** FE-047
- **Review size:** ~120 lines, 4 files, ~12 min

## Goal

`<NowQuestions>` asks "How's your energy?" and "How much time?" as two rows of large chips, prefilled with your last answers, and both can be skipped.

## Why this ticket exists

Decision 2: ask, prefilled, skippable. Remembering the last answer makes the second tap optional, so asking costs one tap or none.

## Read first

- `DESIGN.md`: Chips (line legend) for the pressed/unpressed vocabulary; Buttons.

## Design

- **Pattern:** Presentational component + custom hook `useLastNowAnswer` (per-viewer convenience in `localStorage`, wrapped in try/catch) around pure `parseAnswer` / `serializeAnswer`.

## Packages

None new.

## Details

**Files:** `web/src/features/now/components/NowQuestions.tsx` (new), `web/src/features/now/model/lastAnswer.ts` + `.test.ts` (new), `web/src/features/now/useLastNowAnswer.ts` (new), `web/src/screens.tsx` (changed: dev-only `dev-now`).

```ts
interface NowQuestionsProps {
  readonly value: { energy: Energy | null; availableMinutes: Minutes | null }
  readonly onChange: (v: NowQuestionsProps['value']) => void
  readonly onAsk: () => void
  readonly onSkip: () => void
  readonly busy?: boolean
}
```

- Two labelled rows: `ENERGY` (Low · Medium · High) and `TIME` (5 min · 15 · 30 · 60+). Chips are 44px tall, `aria-pressed`, a second tap clears the choice.
- **Show me** primary (scarlet); **Skip** ghost (asks with nothing set).
- Keyboard: chips are a roving-tabindex group per row (arrow keys), Enter on **Show me**.
- Storage key `now:lastAnswer:v1`; bad JSON or blocked storage → no prefill, never an error.

## Steps

1. `lastAnswer.ts` + tests.
2. Hook.
3. Component + dev screen.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen.

- `parseAnswer ignores bad JSON and unknown values`
- `serialize then parse round-trips`
- `toggling the same chip clears it` (pure `toggle(value, field, option)`)

## Acceptance criteria

- [ ] Choices survive a reload; a private window just starts empty
- [ ] Keyboard-only works
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`#dev-now`: pick Low and 15, reload → still picked; tap 15 again → cleared; tab and arrow through.

## Review guide

1. Storage wrapped in try/catch.
2. Pressed state uses the chip vocabulary, not a new style.

## Out of scope

- Context question → later (default is any context).

## Notes / log
