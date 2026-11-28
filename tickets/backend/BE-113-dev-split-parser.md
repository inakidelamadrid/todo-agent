# BE-113: Dev-only splitter parser (DUMP_PARSER=dev)

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M4 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-090, BE-095
- **Can run in parallel with:** BE-096
- **Public endpoint?** no
- **Review size:** ~70 lines, 4 files, ~8 min

## Goal

With `DUMP_PARSER=dev` in `api/.env` (never in production), dumps are split by a tiny deterministic rule set, so M5–M7 show several confident items without n8n.

## Why this ticket exists

Until M8 (blocked on EPIC-008), every dump becomes one fallback item with confidence 0, so Accept all (M7) and multi-item cards (M5) can't be tried by hand. A plain-Python splitter behind the same `DumpParser` port fixes that, and proves the port works with a second adapter.

## Read first

- `api/app/inbox/parser.py` (BE-090), `api/app/settings.py` (`app_env`, how the playground switch refuses production).

## Design

- **Pattern:** Ports and adapters: a second adapter for the same port, chosen once in the lifespan.

## Packages

None new.

## Details

**Files:** `api/app/inbox/dev_parser.py` (new), `api/app/settings.py` (changed: `dump_parser: Literal["off", "dev", "n8n"] = "off"`), `api/app/main.py` (changed: lifespan picks the parser; startup refuses `dev` when `APP_ENV=production`), `api/.env.example` (changed), `api/tests/test_dev_parser.py` (new).

`dev_split_parser() -> DumpParser`, pure inside:

- Split on newlines, `;`, `, also`, ` and also `, `, y también`; trim; drop empty parts; max 20.
- A part with a number and a money word (`pay`, `paid`, `pagar`, `$`) → `expense` (`amountCents = number * 100`, MXN, description = the part without the number).
- A part starting with `remember`/`recordar` and containing an ISO date → `reminder`.
- Otherwise `task` with the part as title, size `S`.
- `confidence = 0.85`, `source_span = part`.

No dates are interpreted beyond ISO `YYYY-MM-DD` (relative dates are n8n's job).

## Steps

1. Splitter + tests.
2. Setting and lifespan selection with the production guard.

## Tests

- `test_splits_on_commas_also_and_newlines`
- `test_money_part_becomes_expense_in_cents`
- `test_plain_part_becomes_task`
- `test_dev_parser_refused_in_production`

## Acceptance criteria

- [ ] `DUMP_PARSER=dev` → `POST /inbox/dumps` returns several items with `parsed: true`
- [ ] Startup fails with `DUMP_PARSER=dev` and `APP_ENV=production`
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Set `DUMP_PARSER=dev` in `api/.env`, restart `make api-dev`, then:

```bash
curl -s -X POST http://127.0.0.1:8000/inbox/dumps -H "X-API-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"rawText":"call dentist, also buy cat food and also pay gym 600"}' | python3 -m json.tool
```

Three items: two tasks, one expense of `60000` cents.

## Review guide

1. Production guard mirrors the playground's.
2. The splitter is obviously a toy: no regex tower.

## Out of scope

- Real parsing → BE-091 + BE-112 (`DUMP_PARSER=n8n`).

## Notes / log
