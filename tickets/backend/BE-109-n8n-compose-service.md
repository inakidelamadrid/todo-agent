# BE-109: Self-hosted n8n service in docker-compose

- **Status:** done
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.2 · Milestone M1 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** every other EPIC-003 ticket
- **Public endpoint?** no (n8n binds to `127.0.0.1` only)
- **Review size:** ~60 lines, 4 files, ~10 min

## Goal

`docker compose --profile n8n up -d n8n` starts a self-hosted [n8n](https://github.com/n8n-io/n8n) on `127.0.0.1:5678` that keeps its data across restarts and reports healthy.

## Why this ticket exists

EPIC-003 parses brain dumps in n8n (outline, Decisions). Nothing runs n8n yet. This ticket adds the container only; the make targets (BE-110) and the runbook (BE-111) build on it. Putting it behind a compose **profile** keeps `make db-up` exactly as it is today.

## Read first

- `docker-compose.yml`: the Postgres and Redis services this sits next to (pinned image, `127.0.0.1` port, named volume, healthcheck).
- `.env.db.example` and the `check-env` target in `Makefile`: how secrets stay out of the compose file.
- n8n Docker docs: <https://docs.n8n.io/hosting/installation/docker/>, and the environment variable reference: <https://docs.n8n.io/hosting/configuration/environment-variables/>.
- **Compose profiles:** a service with `profiles: [n8n]` starts only when that profile is active (`--profile n8n`), so plain `docker compose up` ignores it. <https://docs.docker.com/compose/how-tos/profiles/>

## Design

- **Pattern:** none; configuration only.
- **Data flow:** `docker compose --profile n8n up` → container reads `.env.n8n` → n8n stores workflows and credentials in the `n8n_data` volume (SQLite) → healthcheck polls `/healthz`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| Docker image `n8nio/n8n` | **new** | the n8n server | Official image. `2.48.7` was the latest stable tag on Docker Hub on 2026-11-22 (amd64 + arm64). Re-check the tag when you build this and pin an exact version, never `latest`. Licence: Sustainable Use License (fair-code): self-hosting for your own internal use is allowed. |

## Details

**Files**

- `docker-compose.yml` (changed): new `n8n` service and `n8n_data` volume.
- `.env.n8n.example` (new): documented placeholders, no real values.
- `.gitignore` (changed): add `.env.n8n`.
- `api/.env.example` (changed): a comment under the n8n block (from BE-038) saying the local value is `N8N_BASE_URL=http://127.0.0.1:5678`.

**Service**

```yaml
  n8n:
    image: n8nio/n8n:2.48.7        # exact tag; check Docker Hub when building
    profiles: [n8n]
    restart: unless-stopped
    env_file: .env.n8n
    ports:
      - "127.0.0.1:${N8N_PORT:-5678}:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:5678/healthz >/dev/null || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 12
```

**`.env.n8n.example`**

| Variable | Value | Why |
|---|---|---|
| `N8N_ENCRYPTION_KEY` | `change-me` (replace with 32+ random chars: `openssl rand -hex 32`) | Encrypts stored credentials. Losing it makes saved credentials unreadable. |
| `GENERIC_TIMEZONE` / `TZ` | `America/Mexico_City` | Dates in workflows match the app's timezone |
| `N8N_HOST` / `N8N_PORT` / `N8N_PROTOCOL` | `127.0.0.1` / `5678` / `http` | Local only |
| `N8N_SECURE_COOKIE` | `false` | Needed for the login cookie over plain `http://127.0.0.1`; production must use HTTPS and `true` |
| `N8N_DIAGNOSTICS_ENABLED` / `N8N_PERSONALIZATION_ENABLED` | `false` | No telemetry leaves the machine |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE` | `true` | Code nodes can't read container env vars |
| `N8N_RUNNERS_ENABLED` | `true` | Code nodes run in the task runner, isolated from the main process |
| `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` | `true` | Settings file is `0600` |

The database is n8n's default SQLite inside the volume. Postgres for n8n is a production-hosting decision (not decided).

## Steps

1. Check the current stable tag on Docker Hub; pin it.
2. Add the service, volume and env example; gitignore `.env.n8n`.
3. Inside the pinned image, confirm `wget` exists and `/healthz` returns 200; if not, switch the healthcheck to `node -e "fetch('http://127.0.0.1:5678/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"` and note it here.
4. Confirm `make db-up` / `make db-down` behave exactly as before.

## Tests

No pytest. The checks are the commands below.

## Acceptance criteria

- [ ] `docker compose --env-file .env.db --profile n8n up -d --wait n8n` ends with n8n `healthy`
- [ ] The port is bound to `127.0.0.1` only (`docker compose ps` shows `127.0.0.1:5678->5678`)
- [ ] Workflows survive `down` + `up` (named volume)
- [ ] `make db-up` does not start n8n
- [ ] No secret in `docker-compose.yml`; `.env.n8n` is gitignored
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cp .env.n8n.example .env.n8n   # then set N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
docker compose --env-file .env.db --profile n8n up -d --wait n8n
docker compose --env-file .env.db ps
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5678/healthz   # 200
```

Open <http://127.0.0.1:5678>: the owner sign-up screen appears.

## Review guide

1. `docker-compose.yml`: exact image tag? `127.0.0.1` binding? `profiles: [n8n]`?
2. `.env.n8n.example`: placeholders only, each line explained, telemetry off.
3. `.gitignore`: `.env.n8n` present.

Things that should *not* be in the diff: make targets (BE-110), workflows (BE-112), any change to the API.

## Out of scope

- `make n8n-*` targets → BE-110.
- Owner account, credentials, import/export → BE-111.
- Production hosting, HTTPS, Postgres for n8n → undecided.

## Assumptions

- `/healthz` and `wget` exist in the pinned image; step 3 checks and gives the fallback.

## Notes / log

- Pinned `n8nio/n8n:2.49.8` after checking Docker Hub stable tag.
- Healthcheck uses `wget` (present in the pinned image; container reached healthy).
- Verified `make db-up` does not start n8n, the port binds to `127.0.0.1:5678`, and data survives `make n8n-down && make n8n-up` via the named `n8n_data` volume.
