# BE-014: Router: caption keywords

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Router step 4
- **Assigned agent / harness / model:**
- **Depends on:** BE-013
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files, ~8 min

## Goal

A photo or document whose caption starts with a known keyword routes straight to that feature instead of asking what it is.

## Why this ticket exists

It is the fast path for "I know what this is": caption a photo `vault` and it is filed. It is a second small dictionary next to the command table, added on its own so the ordering rule (commands before keywords) is visible in one diff.

## Read first

- `api/app/telegram/routing.py` from BE-013.

## Design

- **Pattern:** Strategy as a dictionary, same as the command table.
- **Data flow:** `InboundUpdate` (PHOTO/DOCUMENT with caption) → first word, lower-cased → `KEYWORDS` → `Route(kind="keyword")`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `api/app/telegram/routing.py` (changed).
- `api/tests/test_telegram_routing.py` (changed).

**Keyword table** (`KEYWORDS: Mapping[str, str]`, immutable):

| Keyword | Target |
|---|---|
| `vault` | `vault.store` |
| `gasto` | `expenses.capture` |
| `expense` | `expenses.capture` |
| `receipt` | `expenses.capture` |
| `note` | `braindump.capture` |

**Function (pure)**

```python
def keyword_of(caption: str | None) -> str | None
```
Returns the first whitespace-separated word, lower-cased, with trailing punctuation (`.,:;!`) stripped, when it is a key of `KEYWORDS`; otherwise `None`.

**`route` change.** For `PHOTO` and `DOCUMENT` only, before the default: if `keyword_of(update.caption)` matches → `Route("keyword", KEYWORDS[kw])`. Text messages are not keyword-routed: free text goes to the brain dump, whose AI split decides (epic §5.2).

## Steps

1. Add `KEYWORDS` and `keyword_of` with tests.
2. Insert the step in `route`.

## Tests

- `test_keyword_of_matches_first_word_case_insensitively`: `"Vault: passport"` → `"vault"`.
- `test_keyword_of_ignores_keyword_in_the_middle`: `"my vault"` → `None`.
- `test_photo_with_vault_caption_routes_to_vault` (uses `photo.json`).
- `test_photo_without_caption_still_asks_to_classify`
- `test_text_message_starting_with_keyword_goes_to_braindump`

## Acceptance criteria

- [ ] Captioned media with a leading keyword routes to the keyword's target
- [ ] Text messages are unaffected
- [ ] Commands and callbacks still take precedence
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make api-test
```

## Review guide

Read the diff in this order, and check:

1. The position of the new step inside `route`.
2. `keyword_of`: first word only.

Things that should *not* be in the diff: any handler; any AI classification.

## Out of scope

- The "Receipt, document or note?" question itself → the `media.classify` handler, owned by EPIC-006/EPIC-002.
- Pending mode → BE-016.

## Assumptions

- The keyword list is my reading of the epic's two examples (`vault`, `gasto`) plus English equivalents, since replies are in English (question 4). Edit the table freely.

## Notes / log

The agent adds progress notes, decisions and open questions here.
