# BE-110: Make targets to start, stop and check n8n

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M1 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-109
- **Can run in parallel with:** M2–M7 tickets
- **Public endpoint?** no
- **Review size:** ~70 lines, 1 file, ~8 min

## Goal

`make n8n-up`, `n8n-down`, `n8n-status`, `n8n-logs` and `n8n-check` manage the local n8n, and `n8n-check` tells you in one glance whether n8n is healthy, ready and wired to the API.

## Why this ticket exists

BE-109 added the container; this ticket gives it the same short commands Postgres and Redis already have (`db-up`, `db-status`, …). `n8n-check` is the M1 demo and the first thing to run when M8 parsing doesn't work.

## Read first

- `Makefile`: `check-env`, `db-up`, `db-status`, `db-logs`, `telegram-check`, and the `help` target (every public target has a `## description`).
- n8n health endpoints: <https://docs.n8n.io/hosting/logging-monitoring/monitoring/> (`/healthz` = process up, `/healthz/readiness` = database reachable).

## Design

- **Pattern:** none; small shell recipes, like the existing targets.
- **Data flow:** `make n8n-check` → `curl` two local URLs → read `N8N_BASE_URL` from `api/.env` (name only compared, never printed beyond the URL) → ✓/✗ lines.

## Packages

None new (`curl` and Docker Compose are already required).

## Details

**File:** `Makefile` (changed). Add all targets to `.PHONY` and give each a `##` help line.

| Target | Behaviour |
|---|---|
| `check-n8n-env` (internal, no `##`) | `.env.n8n` must exist; `N8N_ENCRYPTION_KEY` must not be empty, `change-me`, or shorter than 32 characters. Clear ✗ message with the fix, like `check-env`. |
| `n8n-up` | `check-env check-n8n-env`, then `$(COMPOSE) --profile n8n up -d --wait n8n`, then `✓ n8n is up: http://127.0.0.1:5678` |
| `n8n-down` | `$(COMPOSE) --profile n8n stop n8n` (data kept) |
| `n8n-status` | `$(COMPOSE) --profile n8n ps n8n` |
| `n8n-logs` | `$(COMPOSE) --profile n8n logs -f n8n` |
| `n8n-check` | Prints three lines and exits non-zero if any fails (see below) |

**`n8n-check` output**

```
✓ n8n health      http://127.0.0.1:5678/healthz
✓ n8n readiness   http://127.0.0.1:5678/healthz/readiness
✓ api/.env        N8N_BASE_URL points at http://127.0.0.1:5678
```

Failures print `✗` and a hint: `run: make n8n-up`; `N8N_BASE_URL is not set in api/.env`; `N8N_BASE_URL is <url>, expected http://127.0.0.1:5678`. It never prints `N8N_SHARED_SECRET` or any other value except the base URL. The port comes from `N8N_PORT` in `.env.n8n` (default 5678).

## Steps

1. `check-n8n-env`.
2. `n8n-up`, `n8n-down`, `n8n-status`, `n8n-logs`.
3. `n8n-check`.
4. Run `make help` and confirm the new lines read well.

## Tests

No pytest; shell recipes are checked by hand below.

## Acceptance criteria

- [ ] `make n8n-up` refuses to start with a missing or `change-me` encryption key, and says how to fix it
- [ ] `make n8n-up` waits until healthy, then prints the URL
- [ ] `make n8n-check` prints ✓ ✓ ✓ with n8n running and `N8N_BASE_URL=http://127.0.0.1:5678` in `api/.env`
- [ ] With n8n stopped, `make n8n-check` prints ✗ with `run: make n8n-up` and exits non-zero
- [ ] No target prints a secret
- [ ] `make help` lists the five public targets
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
make n8n-up && make n8n-check     # ✓ ✓ ✓
make n8n-down && make n8n-check   # ✗ … run: make n8n-up   (exit 2)
make help | grep n8n
```

## Review guide

1. `check-n8n-env`: same style as `check-env`; never echoes the key.
2. `n8n-check`: does it read `api/.env` without printing anything but the URL?
3. Every recipe uses `--profile n8n`.

Things that should *not* be in the diff: compose changes (BE-109), workflow import/export (BE-111).

## Out of scope

- Import, export and backup commands → documented in BE-111.

## Notes / log
