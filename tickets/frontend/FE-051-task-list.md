# FE-051: Task list (presentational)

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.4, §6 · Milestone M3 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-031, FE-040
- **Can run in parallel with:** FE-032
- **Review size:** ~140 lines, 4 files, ~12 min

## Goal

`<TaskList>` renders grouped active tasks with Done and Let go actions in every state (loading, error, empty, populated), from fixture data, on a dev-only screen.

## Why this ticket exists

Accepted inbox items need somewhere to live. The component is built and polished alone, against fixtures, so its review is about look and states; FE-052 connects it.

## Read first

- `DESIGN.md`: Cards, Buttons (outline vs ghost), Status tags, The Signage Rule, The One Scarlet Rule.
- `web/src/features/bills/components/BillTable.tsx` and `LoadStates.tsx`: row rhythm, stacked list under 768px, load states.

## Design

- **Pattern:** Presentational component: props in, callbacks out, no store.

## Packages

None new (`lucide-react` icons are installed).

## Details

**Files:** `web/src/features/tasks/components/TaskList.tsx` (new), `web/src/features/tasks/fixtures.ts` (new), `web/src/screens.tsx` (changed: add dev-only `dev-tasks` entry rendering fixtures with a state switcher).

```ts
interface TaskListProps {
  readonly status: 'loading' | 'error' | 'ready'
  readonly errorMessage?: string
  readonly groups: ReturnType<typeof groupByDoDate>
  readonly today: DateKey
  readonly busyIds?: ReadonlySet<string>
  readonly onComplete: (id: string) => void
  readonly onDrop: (id: string) => void
  readonly onRetry: () => void
}
```

- **Panel:** card token, hairline, 11.2px radius; header label `TASKS · 7` (condensed, uppercase, tabular count).
- **Group header row:** label (`TODAY`, `UPCOMING`, `ANYTIME`) on the muted surface at 50%.
- **Row:** title (Barlow 600), first step below in muted body text (if any), a size label chip (condensed, `S · 15 MIN`), a context icon (`Home`, `Monitor`, `Phone`, `ShoppingBag`, `Globe`) with an `aria-label`, and `dateLabel` text (muted tone for "Past its date"; tabular figures for dates).
- **Actions:** **Done** as an outline button with a `Check` icon; **Let go** as a ghost button. No scarlet fill here (the page has none). Busy rows dim to 60% and disable their buttons.
- **States:** loading = three skeleton rows; error = calm sentence + **Try again** outline button; empty = "Nothing on your list. Capture something with /." in body text.
- **Phone width:** rows stack; buttons stay 44px tall touch targets.
- **Keyboard:** buttons in DOM order; visible cobalt focus ring.
- **Motion:** row removal fades over 200ms; none under reduced motion.

## Steps

1. Fixtures covering every group, a past-its-date task, a long title, no first step.
2. Component.
3. Dev-only `#dev-tasks` screen with a status switcher.

## Tests

The repo has no component-test library (`@testing-library/react` isn't installed), so, like the playground, the logic is pulled into a pure helper and tested; the component itself is checked by eye on `#dev-tasks`.

- `web/src/features/tasks/model/taskRow.ts` (new): `taskRow(task, today) → { title, firstStep, sizeLabel, contextLabel, date: { text, tone } | null }`.
- `taskRow uses the muted tone for past its date`
- `taskRow hides an empty first step`
- `taskRow labels every context`

## Acceptance criteria

- [ ] Every state above visible on `#dev-tasks` (dev server only)
- [ ] Follows DESIGN.md: no shadows on the page, condensed uppercase labels only, one-scarlet rule respected
- [ ] Works at phone width; keyboard-only works
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make web-dev`, open `http://127.0.0.1:5173/#dev-tasks`, flip the state switcher through loading → error → empty → ready, in dark and light, at 375px and desktop.

## Review guide

1. Colours: is "Past its date" muted?
2. Buttons: outline/ghost only.
3. `screens.tsx`: entry marked `devOnly`.

Things that should *not* be in the diff: store, API calls.

## Out of scope

- Wiring and the `#tasks` nav item → FE-052.
- Editing tasks inline → later.

## Notes / log
