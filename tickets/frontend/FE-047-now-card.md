# FE-047: What now? card and the kind reset

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 stories 10, 12; §6 · Milestone M10 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-045, FE-040
- **Can run in parallel with:** FE-046
- **Review size:** ~140 lines, 3 files, ~12 min

## Goal

`<NowCard>` shows one task large and alone (title, first step, *why*, Start · Another · Not today), plus a gentle "take a break" variant and a kind 2-minute reset when nothing fits.

## Why this ticket exists

This screen is the epic's heart: "deliberately minimal to lower overwhelm" (§6). It is designed alone, against fixtures, before any flow logic.

## Read first

- Epic §6 What now? screen and Design notes (the choice is "the highlighted next station").
- `DESIGN.md`: Display type, The One Scarlet Rule, Network Map station vocabulary, Motion.

## Design

- **Pattern:** Presentational component with three variants via a discriminated `view` prop.

## Packages

None new.

## Details

**Files:** `web/src/features/now/components/NowCard.tsx` (new), `web/src/features/now/fixtures.ts` (new), `web/src/screens.tsx` (changed: `dev-now` shows the card variants).

```ts
type NowCardView =
  | { kind: 'pick'; pick: NowPick; rerollsLeft: number }
  | { kind: 'break' }          // after 3 rerolls
  | { kind: 'nothing-fits' }
interface NowCardProps { readonly view: NowCardView; readonly busy?: boolean
  readonly onStart: () => void; readonly onAnother: () => void; readonly onNotToday: () => void; readonly onAskAgain: () => void }
```

- **Pick:** one centred card, max 40rem. A short horizontal line with a single ringed station at its end (the "next station"), then `NEXT` label, the title in Display (2.25rem phone / 3rem desktop, tight tracking), `FIRST STEP` label with the first step in 1.125rem body (prominent), the *why* in muted body. Three big buttons (48px): **Start** primary scarlet, **Another** outline (with "2 left" muted), **Not today** ghost. No list or other task visible.
- **Break:** "That's three. Maybe a two-minute break first?" + **Ask again** outline.
- **Nothing fits:** "Nothing fits right now, and that's fine." + "Two-minute reset: a glass of water, a stretch, three slow breaths." + **Ask again** outline.
- **Motion:** card fades up 8px over 200ms when the pick changes; static under reduced motion.
- Language: "Not today", never "Skip"; no guilt words.

## Steps

1. Fixtures (long title, empty first step, each variant).
2. Component + dev screen.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen. Pure `anotherLabel(rerollsLeft)` → "Another · 2 left": test `label counts down and hides at 0`.

## Acceptance criteria

- [ ] Each variant looks right on `#dev-now` in dark and light, desktop and 375px
- [ ] Exactly one scarlet button; no other tasks visible
- [ ] Reduced motion respected
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`#dev-now`: flip through pick / break / nothing-fits; try a 90-character title at 375px.

## Review guide

1. Copy: kind, neutral, matches the epic.
2. Hierarchy: title → first step → why.

## Out of scope

- Flow and API → FE-048.

## Notes / log
