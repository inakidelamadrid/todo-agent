# FE-039: Inbox list with loading, error and inbox-zero states

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.3, §6 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-038
- **Can run in parallel with:** FE-037
- **Review size:** ~110 lines, 3 files, ~10 min

## Goal

`<InboxList>` lays out the cards and owns the list-level states: loading, error, and a calm, quietly celebratory inbox zero.

## Why this ticket exists

The empty state matters in this epic: "Inbox zero is calm and celebratory, without streak language" (§5.3). It gets its own small review.

## Read first

- `web/src/features/bills/components/EmptyState.tsx`, `LoadStates.tsx`.
- `DESIGN.md`: Network Map vocabulary (a single ringed station can be the inbox-zero mark).

## Design

- **Pattern:** Presentational component; renders cards via a `renderItem` prop so it stays unaware of handlers.

## Packages

None new.

## Details

**Files:** `web/src/features/inbox/components/InboxList.tsx` (new), `web/src/features/inbox/components/InboxZero.tsx` (new), `web/src/screens.tsx` (changed: `dev-inbox` gets a state switcher).

```ts
interface InboxListProps {
  readonly status: 'loading' | 'error' | 'ready'
  readonly errorMessage?: string
  readonly items: readonly InboxItem[]
  readonly header?: ReactNode            // FE-044 puts Accept all here
  readonly renderItem: (item: InboxItem) => ReactNode
  readonly onRetry: () => void
}
```

- **Header:** `INBOX · 5` (condensed label, tabular count). No red counter, ever.
- **Loading:** three card skeletons.
- **Error:** "Couldn't load your inbox." + **Try again** outline.
- **Inbox zero:** a small SVG station ring in the paid colour on a short line, title "All clear", body "Nothing waiting on you. Capture anything with /." No streaks, no counts of past days.
- **Spacing:** cards on a 12px gap; 20px gutter around the panel.

## Steps

1. `InboxZero`.
2. `InboxList`.
3. Dev screen switcher.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen. Pure helper: `inboxHeader(count)` → `INBOX · 5`, test `header shows the count without warning styles` (returns text only).

## Acceptance criteria

- [ ] All four states visible on `#dev-inbox`
- [ ] Inbox zero has no streak or guilt language
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`#dev-inbox` → switch states; check inbox zero in dark and light at 375px.

## Review guide

1. Inbox zero copy and colour.

## Out of scope

- Data and screen → FE-041.

## Notes / log
