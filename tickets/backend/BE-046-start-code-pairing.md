# BE-046: Pair the bot with a one-time /start code

- **Status:** blocked (deferred by owner for further investigation; open question 3)
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.2 Allowlist, open question 3
- **Assigned agent / harness / model:**
- **Depends on:** BE-009, BE-021, F-1
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** to be estimated; likely two or three tickets

## Goal

The bot learns which Telegram account is the owner through a one-time code, replacing the `TELEGRAM_ALLOWED_USER_ID` environment variable.

## Why this ticket exists

You chose pairing over a hard-coded ID and deferred the design. This ticket records the decision and the questions to settle, so the interim environment variable (BE-004, BE-009) is clearly temporary.

## Read first

- `api/app/telegram/allowlist.py`: `is_allowed` takes the allowed ID as an argument, so only its source changes.
- https://core.telegram.org/bots/features#deep-linking: `https://t.me/<bot>?start=<code>` sends `/start <code>`.

## Design

- **Pattern:** To be decided. Likely: a single-use, short-lived token (hashed at rest) plus a one-row owner table.
- **Data flow:** web app (logged in) → `POST /integrations/telegram/pairing` → code → user opens the deep link → `/start <code>` → verify → store owner ID.

## Packages

None new. Standard library and what is already installed.

## Details

Not ready for implementation. Questions to answer first:

1. Who may request a code? It needs a logged-in user, so it depends on **F-1 User login**; an API key alone should not be enough to re-pair the bot.
2. Code format and lifetime (proposal: 32 random bytes, base64url, valid 10 minutes, single use, stored as a SHA-256 hash).
3. Where the owner ID lives (proposal: a one-row `telegram_owner` table, like `notification_policy`).
4. Re-pairing and unpairing: what happens to the old account, and to queued messages.
5. `/start` must be handled **before** the allowlist for this one case, without revealing to strangers whether a code was valid. This is the delicate part and the reason for the investigation.

When answered, split into: code issue endpoint; `/start` verification; switching `is_allowed`'s source and removing the environment variable.

## Steps

1. Answer the five questions with the owner.
2. Rewrite this ticket into two or three implementable ones.

## Tests

- To be listed when unblocked. At minimum: a used code cannot be reused; an expired code fails; a wrong code and a stranger's `/start` are indistinguishable from outside.

## Acceptance criteria

- [ ] The five questions are answered in this ticket
- [ ] It has been split into implementable tickets and approved
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

To be written when unblocked.

## Review guide

Read the diff in this order, and check:

1. To be written when unblocked.

Things that should *not* be in the diff: anything, until unblocked.

## Out of scope

- User login → F-1.

## Notes / log

The agent adds progress notes, decisions and open questions here.
