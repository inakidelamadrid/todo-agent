# FE-035: Global keyboard shortcut helper and hook

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §6 (keyboard-first) · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** everything
- **Review size:** ~60 lines, 2 files, ~6 min

## Goal

`useShortcut('/', handler)` runs `handler` when `/` is pressed anywhere, except while typing in a field.

## Why this ticket exists

The epic wants `/` for Quick add and `n` for What now?. Both need the same rule for when a key press is a shortcut. One pure predicate, tested, then a tiny hook.

## Read first

- `web/src/lib/screen.ts`: how a small side effect is wrapped around a pure function.

## Design

- **Pattern:** Custom hook around a pure predicate.

## Packages

None new.

## Details

**Files:** `web/src/lib/shortcut.ts` (new), `web/src/lib/shortcut.test.ts` (new).

```ts
export interface KeyLike { readonly key: string; readonly metaKey: boolean; readonly ctrlKey: boolean; readonly altKey: boolean;
  readonly isComposing: boolean; readonly target: { readonly tagName?: string; readonly isContentEditable?: boolean } | null }
/** Pure. */
export const shouldHandleShortcut = (e: KeyLike, key: string): boolean
export const useShortcut = (key: string, handler: () => void): void   // keydown on window; preventDefault when handled
```

False when: different key; any of meta/ctrl/alt held; `isComposing`; target is `INPUT`, `TEXTAREA`, `SELECT` or content-editable.

## Steps

1. Predicate + tests.
2. Hook.

## Tests

- `handles / on the page body`
- `ignores / inside an input and a textarea`
- `ignores / with ctrl or meta`
- `ignores keys during IME composition`

## Acceptance criteria

- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
npm --prefix web test -- shortcut
```

## Review guide

1. The predicate covers every case in the list.
2. The hook removes its listener on unmount.

## Out of scope

- Using it → FE-037 (`/`), FE-048 (`n`).

## Notes / log
