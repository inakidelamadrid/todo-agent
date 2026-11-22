# FE-027: Template preview panel (presentational, all states)

- **Status:** done
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** FE-020
- **Can run in parallel with:** FE-021 to FE-026
- **Review size:** ~100 lines, 3 files plus tests, ~12 min

## Goal

A panel lets you pick a template, fill its fields, and see the result both as a chat bubble and as the exact HTML source, from props.

## Why this ticket exists

Telegram accepts a small HTML subset. The bubble must show bold, italic and code the way Telegram would, without ever injecting server HTML into the page, so the conversion is a small tested pure function.

## Read first

- `TemplateInfo`, `TemplatePreview` in FE-021's ticket.
- Telegram's HTML style: https://core.telegram.org/bots/api#html-style (we support `b`, `i`, `code` only).
- `DESIGN.md`: Cards / Containers, Typography.

## Design

- **Pattern:** Presentational component plus a pure parser that returns a typed node list (no `dangerouslySetInnerHTML`).
- **Data flow:** `preview.html` → `parseTelegramHtml(html)` → `readonly Node[]` → React elements.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/telegramHtml.ts` (new): `type TgNode = { kind: 'text' | 'b' | 'i' | 'code'; text: string }`; `parseTelegramHtml(html: string): readonly TgNode[]` (pure). Handles `<b>`, `<i>`, `<code>` and the entities `&lt; &gt; &amp;`. Any other tag is shown as literal text. Nesting is not supported; nested input degrades to text.
- `web/src/features/playground/components/TemplatePreviewPanel.tsx` (new): template select; one input per field (from `TemplateInfo.fields`); **Preview**; result: a chat bubble rendering the nodes, the raw HTML in a code block, and the length as 'n / 4096'.
- `web/src/features/playground/telegramHtml.test.ts` (new).

Hand-written instead of a package: an HTML sanitiser would be far heavier than three tags, and the goal is to never render markup at all.

**States:** loading templates, no template chosen, fields incomplete (button disabled), loading preview, error (missing field named, unknown template), result. A template without fields shows 'No fields needed'.

States to polish: loading, empty, error, hover, focus-visible, disabled, phone width, light and dark. Use the tokens and type scale in `DESIGN.md`; this is an internal tool, but not an unstyled one.

## Steps

1. `parseTelegramHtml` with tests.
2. The panel with fixtures.
3. Check every state.

## Tests

- `test_plain_text`.
- `test_bold_italic_code_nodes`.
- `test_entities_are_decoded_in_text`.
- `test_unknown_tag_stays_literal`: `<script>` appears as text.
- `test_escaped_data_inside_code_stays_text`: `<code>/&lt;b&gt;x&lt;/b&gt;</code>` → one code node with text `/<b>x</b>`.

## Acceptance criteria

- [ ] The bubble shows bold, italic and code; everything else is plain text
- [ ] The component uses no `dangerouslySetInnerHTML`
- [ ] The raw HTML and the length are shown
- [ ] All states render from props; nothing fetches
- [ ] Works at 375 px, with the keyboard, in both themes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. Templates tab with fixtures: pick a template with a field, see the bubble and the source.
2. `grep -rn dangerouslySetInnerHTML web/src`: no hits.

## Review guide

Read the diff in this order, and check:

1. `telegramHtml.ts`: can any input produce an element other than `b`, `i`, `code`?
2. Is the panel free of fetching?

Things that should *not* be in the diff: API calls, sending, buttons preview.

## Out of scope

- Wiring → FE-028.
- Sending the previewed template → FE-029.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `telegramHtml.ts`: `parseTelegramHtml` is a regex over `<b>|<i>|<code>` with no inner `<`, so nested or unknown tags stay literal text. No `dangerouslySetInnerHTML` anywhere.
- `TemplatePreviewPanel.tsx` exports `TemplatePicker` (select + one input per field), reused by FE-029, and `ChatBubble`.
- `templateForm.ts`: pure `findTemplate`, `fieldsComplete`, `fieldErrorsFrom` (a 422 naming a field, in `loc` or in the message, maps to it).
- Checked in Chrome with a fake API: empty, loading, result (bold/italic/code/newlines), field error, light and dark, 340 px.
