# FE-006: Telegram status card (presentational, all states)

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-010: Telegram notification policy and outbox](../../Epics/EPIC-010-telegram-notification-policy-outbox.md) (moved from EPIC-008)
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** FE-002 to FE-005
- **Review size:** ~110 lines, 3 files, ~12 min

## Goal

A `TelegramStatusCard` component shows, from props, whether Telegram is connected and healthy.

## Why this ticket exists

It gives the connection a face before any wiring: connected, not configured, unreachable and erroring each need their own calm wording, which is easier to get right against fixtures.

## Read first

- `DESIGN.md`: Midnight Transit tokens, the `label-caps` style, the rail status idiom.
- `web/src/features/bills/components/RailStatus.tsx`: the dot + title + detail idiom this card reuses.
- BE-043: the response shape.

## Design

- **Pattern:** Presentational component over a pure `describeStatus` function.
- **Data flow:** `TelegramStatus` → `describeStatus(status)` → `{ tone, title, detail }` → markup.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/telegram/model/status.ts` (new) and `status.test.ts`.
- `web/src/features/telegram/components/TelegramStatusCard.tsx` (new).

**Types** (`readonly`, matching BE-043)

```ts
export interface TelegramStatus {
  readonly configured: boolean
  readonly reachable: boolean
  readonly webhook: { readonly urlHost: string; readonly pendingUpdateCount: number;
                      readonly lastErrorAt: string | null; readonly lastErrorMessage: string | null } | null
  readonly outbound: { readonly queued: number; readonly deferred: number; readonly failed: number; readonly lastSentAt: string | null }
  readonly updates: { readonly last24h: number; readonly failed24h: number }
}
```

**Pure function** `describeStatus(status): { tone: 'ok' | 'attention' | 'muted'; title: string; detail: string }`

| Condition (first match) | Tone | Title | Detail |
|---|---|---|---|
| not configured | muted | Not connected | Add the bot token to the API |
| not reachable | attention | Can't reach Telegram | The API will keep trying |
| webhook has a last error | attention | Webhook error | the error message, truncated to 80 characters |
| `outbound.failed > 0` | attention | N messages failed | Last sent … |
| otherwise | ok | Connected | N waiting · last sent … |

Tones map to existing tokens (`--paid`, `--due-soon`, `--muted-foreground`); no red alarm styling, per the ADHD conventions.

**Component.** Props: `{ status: TelegramStatus | null; load: 'loading' | 'ready' | 'error'; onRetry: () => void }`. Shows the dot, title and detail, then a quiet definition list: webhook host, waiting, deferred, updates in 24 h. States: loading skeleton; error with Retry; ready. `role="status"`. Works at phone width.

## Steps

1. Types and `describeStatus` with one test per table row.
2. The card with fixture props.
3. States and polish.

## Tests

- One test per row of the table.
- `truncates a long webhook error to 80 characters`
- `uses 'attention', never an alarm tone, for failures`

## Acceptance criteria

- [ ] `describeStatus` is pure and covers every row
- [ ] The card renders loading, error and ready states at desktop and phone widths, light and dark
- [ ] No new colour tokens
- [ ] Checked in the browser at desktop and mobile widths
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make web-test
```

Render the card with a fixture for each table row and compare the wording.

## Review guide

Read the diff in this order, and check:

1. The table against `describeStatus`.
2. Wording: calm, factual.
3. The card takes props only.

Things that should *not* be in the diff: fetching; the rail chip.

## Out of scope

- Fetching and placement → FE-007.

## Notes / log

The agent adds progress notes, decisions and open questions here.
