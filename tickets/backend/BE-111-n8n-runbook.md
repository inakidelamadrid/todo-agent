# BE-111: RUNBOOK-n8n-setup.md

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M1 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-110
- **Can run in parallel with:** M2–M7 tickets
- **Public endpoint?** no
- **Review size:** ~120 lines of docs, 1 file, ~10 min

## Goal

One runbook takes you from nothing to a signed-in local n8n with the HMAC credential ready, and covers import, export, backup and upgrades.

## Why this ticket exists

n8n's state (owner account, credentials, workflows) lives in its UI and volume, not in code. Without written steps, rebuilding it after a `docker volume rm` is guesswork. This closes M1; BE-112 follows it to build the parsing workflow.

## Read first

- `RUNBOOK-telegram-setup.md`, `RUNBOOK-clerk-setup.md`: the house runbook style (numbered steps, exact commands, "you should see").
- `integrations/n8n/README.md` (BE-041): the request-signing contract. Link to it; don't repeat it.
- n8n CLI export/import: <https://docs.n8n.io/hosting/cli-commands/>.

## Design

- **Pattern:** none; documentation.

## Packages

None new.

## Details

**File:** `RUNBOOK-n8n-setup.md` (new, repo root). Sections:

1. **What n8n does here** (three lines): the API calls n8n with HMAC-signed requests to transcribe, OCR and parse dumps; n8n only answers; it never writes to the app's database.
2. **First run**: `cp .env.n8n.example .env.n8n`; generate the key (`openssl rand -hex 32`); store a copy of the key in your password manager (losing it loses saved credentials); `make n8n-up`; open <http://127.0.0.1:5678>; create the owner account (strong password, your email); n8n has no public sign-up on a self-hosted instance with an owner.
3. **The shared secret**: generate `N8N_SHARED_SECRET` (`openssl rand -hex 32`), put it in `api/.env` with `N8N_BASE_URL=http://127.0.0.1:5678`, and in n8n create a credential (type *Header Auth* or a *Custom* credential named `todo-agent-hmac`) holding the same value. Workflows read the secret from the credential, never from env (env access is blocked, BE-109).
4. **LLM provider key**: create it as an n8n credential (e.g. *Anthropic* / *OpenAI*). Never put it in the repo or `api/.env`.
5. **Import a workflow**: UI → *Import from file* → `integrations/n8n/workflows/<name>.json`, then attach the credentials from 3 and 4, then activate.
6. **Export a workflow**: `docker compose --env-file .env.db --profile n8n exec n8n n8n export:workflow --id=<id> --output=/tmp/w.json`, then `docker compose … cp n8n:/tmp/w.json integrations/n8n/workflows/<name>.json`. **Check for credentials before committing**; the BE-041 test fails if any slipped in.
7. **Backup**: `n8n export:workflow --all --backup --output=/tmp/backup/` and `n8n export:credentials --all --output=/tmp/creds.json` (encrypted with the key; keep outside the repo).
8. **Upgrade**: read the release notes, bump the tag in `docker-compose.yml`, `make n8n-down && make n8n-up`, `make n8n-check`. Roll back by restoring the previous tag (back up first).
9. **Troubleshooting**: `make n8n-check` meanings; "credentials could not be decrypted" = wrong `N8N_ENCRYPTION_KEY`; login loops = `N8N_SECURE_COOKIE` over http.
10. **Licence note**: Sustainable Use License: fine for this personal, self-hosted use; don't resell it or offer it as a service.

## Steps

1. Write the runbook.
2. Follow it end to end on a fresh volume (`docker volume rm todo-agent_n8n_data` after `make n8n-down`) and fix every step that didn't match.

## Tests

None (docs). The check is the clean-volume run.

## Acceptance criteria

- [ ] Following the runbook on an empty volume ends with you signed in, `todo-agent-hmac` credential created, and `make n8n-check` ✓ ✓ ✓
- [ ] Export instructions warn about credentials and point at the BE-041 test
- [ ] No real secret, email or key in the file
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Do the clean-volume run yourself; every command should work as pasted.

## Review guide

1. First run and shared secret: could you do it from the doc alone?
2. Export: does it say to check for credentials?
3. Nothing duplicates the signing contract from `integrations/n8n/README.md`.

Things that should *not* be in the diff: workflow JSON (BE-112), compose or Makefile changes.

## Out of scope

- Building the `parse_dump` workflow → BE-112.
- Production hosting → undecided.

## Notes / log
