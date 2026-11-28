# FE-036: Quick add field (presentational)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 4, §5.1 · Milestone M5 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-040
- **Can run in parallel with:** FE-033, FE-035
- **Review size:** ~110 lines, 4 files, ~12 min

## Goal

`<QuickAdd>` is a calm, centred capture dialog with a multi-line field, in every state, shown with fixture props on `#dev-quick-add`.

## Why this ticket exists

Capture must cost almost nothing (the epic's first principle). The dialog's look and keyboard behaviour get their own review before it touches the API (FE-037).

## Read first

- `DESIGN.md`: Inputs / Fields, Buttons, Shadow Vocabulary (a floating layer may cast `shadow-lg`), Motion.
- `web/src/components/ui/sheet.tsx`, `alert-dialog.tsx`: the Base UI shadcn components already installed.

## Design

- **Pattern:** Presentational component (props in, callbacks out).

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| shadcn `dialog` and `textarea` components | new files via `npx shadcn add dialog textarea` | the dialog shell and field | Same Base UI primitives as the existing components; no new npm dependency expected (check the diff of `package.json` stays empty; if the CLI adds one, note it here) |

## Details

**Files:** `web/src/components/ui/dialog.tsx`, `web/src/components/ui/textarea.tsx` (generated), `web/src/features/inbox/components/QuickAdd.tsx` (new), `web/src/features/inbox/model/quickAdd.ts` + `quickAdd.test.ts` (new: pure helpers), `web/src/screens.tsx` (changed: dev-only `dev-quick-add`).

```ts
interface QuickAddProps {
  readonly open: boolean
  readonly value: string
  readonly status: 'idle' | 'sending' | 'error'
  readonly errorMessage?: string
  readonly onChange: (value: string) => void
  readonly onSubmit: () => void
  readonly onOpenChange: (open: boolean) => void
}
```

- **Layout:** dialog anchored at 20vh from the top, max 36rem wide, popover token, `shadow-lg` over the 10% backdrop; full width minus 16px gutters on phones.
- **Title:** `CAPTURE` label (condensed, uppercase). Placeholder: "Anything on your mind. One thought or ten."
- **Field:** auto-growing textarea, 3–10 rows, Barlow body size, scarlet caret, cobalt focus ring.
- **Footer:** hint `⌘↵ to save · Esc to close` in muted text (`Ctrl` on non-Mac, from `navigator.platform`); **Save** primary (the only scarlet in the dialog).
- **Keys:** Enter = newline; ⌘/Ctrl+Enter = submit; Esc = close (keeps the text).
- **States:** idle; sending (button shows a spinner, field read-only); error (destructive message under the field, text kept); disabled Save when `value.trim()` is empty; counter `3,812 / 4,000` appears after 3,500 characters (tabular).
- **Motion:** 150ms fade/scale in; none under reduced motion.

Pure helpers: `canSubmit(value)`, `counterText(value)` (or `null` under 3,500), `isSubmitKey(e)`.

## Steps

1. `npx shadcn add dialog textarea`.
2. Pure helpers + tests.
3. Component and dev screen with a state switcher.

## Tests

The repo has no component-test library, so logic lives in pure helpers that are unit-tested; the component is checked by eye on its dev screen.

- `canSubmit is false for whitespace`
- `counter appears after 3500 characters`
- `isSubmitKey accepts meta+Enter and ctrl+Enter, not Enter`

## Acceptance criteria

- [ ] Every state visible on `#dev-quick-add`
- [ ] Keyboard: focus lands in the field on open, Esc closes, ⌘/Ctrl+Enter submits
- [ ] DESIGN.md respected (one scarlet, floating-layer shadow only)
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] Checked in the browser at desktop and mobile widths
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

`make web-dev` → `#dev-quick-add`: switch idle/sending/error, paste 3,600 characters, try the keys, dark and light, 375px.

## Review guide

1. Generated `ui/` files untouched beyond the CLI output.
2. Keys behave as listed.

Things that should *not* be in the diff: API calls, global shortcut.

## Out of scope

- `/` shortcut and posting → FE-037.

## Notes / log
