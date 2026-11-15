# BE-034: Fall back to email when Telegram stays unreachable

- **Status:** blocked (needs EPIC-007 Email integration and BE-031; you answered yes to the fallback and deferred it)
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.3 Failure handling, open question 6
- **Assigned agent / harness / model:**
- **Depends on:** BE-031, BE-032, EPIC-007
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~70 lines, 2 files, ~10 min

## Goal

A message in an important category that could not be delivered by Telegram for longer than a set time is sent by email instead, once.

## Why this ticket exists

Recorded now so the decision is not lost. It cannot be detailed until EPIC-007 defines the email service's send function.

## Read first

- `Epics/EPIC-007-email-integration.md`.
- `api/app/telegram/delivery.py` (BE-031).

## Design

- **Pattern:** Strategy: a per-category mapping decides whether a failed message has a fallback channel.
- **Data flow:** `failed` row in a fallback category, older than N minutes → email service send (same idempotency key) → mark `sent` via email.

## Packages

None new. Standard library and what is already installed.

## Details

To be completed when EPIC-007 is unfolded. Decisions needed then:

- Which categories count as important (a policy field, like `urgent_categories`).
- N: how long Telegram must be unreachable (the epic says "N minutes"; propose 30).
- Whether the outbox row gains a `channel` column or email gets its own outbox.

Fixed already: the email reuses the Telegram message's `idempotency_key` so a recovery cannot send both.

## Steps

1. Re-read this ticket against the finished EPIC-007 tickets and rewrite Details.
2. Implement.

## Tests

- To be listed when unblocked. At minimum: fallback sends once; a recovered Telegram does not double-send; non-important categories never fall back.

## Acceptance criteria

- [ ] Rewritten and approved after EPIC-007 is in tickets
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

To be written when unblocked.

## Review guide

Read the diff in this order, and check:

1. To be written when unblocked.

Things that should *not* be in the diff: anything, until unblocked.

## Out of scope

- The email channel itself → EPIC-007.

## Notes / log

The agent adds progress notes, decisions and open questions here.
