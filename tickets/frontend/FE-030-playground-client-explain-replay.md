# FE-030: Playground client, part 3: explain and replay

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-011: Telegram debugger: explain and replay](../../Epics/EPIC-011-telegram-debugger-explain-replay.md)
- **Assigned agent / harness / model:**
- **Depends on:** FE-021, BE-074, BE-076
- **Can run in parallel with:** FE-022 to FE-029
- **Review size:** ~60 lines, 2 files plus tests, ~10 min

## Goal

Typed client functions exist for the explain and replay actions, including the one that requires `confirm: true`.

## Why this ticket exists

Split out of FE-022 on 2026-11-22, when explain and replay moved to EPIC-011, so the test-message client does not wait on them. Kept apart from the read-only client so the reviewer sees the side-effecting call on its own, and can check that the client never sends `confirm` by itself.

## Read first

- `web/src/features/playground/api.ts` and `types.ts` (FE-021).
- The request and response shapes in BE-072, BE-074, BE-076.

## Design

- **Pattern:** Typed client functions; the confirmation is an explicit argument, never a default.
- **Data flow:** `replay(update, { confirmed: true })` → `POST /admin/telegram/replay` with `confirm: true`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/playground/types.ts` (changed):
  - `ComposedUpdate { kind: 'text' | 'command' | 'photo' | 'document' | 'voice'; text?: string; caption?: string }`
  - `ExplainStep { name: 'allowlist' | 'idempotency' | 'route'; verdict: 'pass' | 'stop' | 'skipped'; detail: string }`
  - `RouteExplanation { steps: readonly ExplainStep[]; finalRoute: { kind: string; target: string; arg: string } | null }`
  - `ReplayResult { updateId: number; status: 'ignored' | 'duplicate' | 'processed' | 'failed'; route: string }`
- `web/src/features/playground/api.ts` (changed): `listSamples()`, `explain(input: { update: ComposedUpdate } | { sample: string })`, `replay(input, opts: { confirmed: true })`.
- `validateComposed(c: ComposedUpdate): FieldErrors` (pure, in `types.ts` or `compose.ts`): the same rules as the API (text required for text and command; a command starts with `/`; text ≤ 4096; caption ≤ 1024, only for photo and document), so the form can show errors before sending.

`replay` has no overload without `{ confirmed: true }`: the type system makes an unconfirmed call a compile error.

## Steps

1. Types and `validateComposed` with tests.
2. Client functions with tests.
3. `make web-test`, `make web-build`.

## Tests

- `test_validate_composed_rules`: one case per rule.
- `test_explain_posts_update_or_sample`.
- `test_replay_sends_confirm_true`.
- `test_409_surfaces_as_api_error_with_detail`.

## Acceptance criteria

- [ ] The three functions are typed and tested
- [ ] `replay` cannot be called without `{ confirmed: true }`
- [ ] `validateComposed` mirrors the API rules
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-test` and `make web-build`: green.

## Review guide

Read the diff in this order, and check:

1. `api.ts`: where is `confirm: true` set, and can it be set without the caller saying so?
2. Do the validation rules match BE-072?

Things that should *not* be in the diff: UI, stores.

## Out of scope

- Wiring → FE-026.

## Notes / log

The agent adds progress notes, decisions and open questions here.
