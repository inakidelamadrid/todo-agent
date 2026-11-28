# n8n Setup Runbook

How to run a self-hosted [n8n](https://github.com/n8n-io/n8n) instance on
`127.0.0.1:5678` for brain-dump parsing. All secrets live in gitignored env
files and n8n credentials — never in the repo.

## What n8n does here

The API calls n8n with HMAC-signed requests to transcribe, OCR and parse
dumps. n8n only answers; it never writes to the app's database. The
request-signing contract lives in `integrations/n8n/README.md` — read it
before creating credentials.

## First run

1. Copy the n8n env file and generate an encryption key:

   ```bash
   cp .env.n8n.example .env.n8n
   # macOS / Linux
   sed -i '' "s/^N8N_ENCRYPTION_KEY=change-me/N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)/" .env.n8n
   # Linux (GNU sed) alternative:
   # sed -i "s/^N8N_ENCRYPTION_KEY=change-me/N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)/" .env.n8n
   ```

   Store a copy of `N8N_ENCRYPTION_KEY` in your password manager. Losing it
   makes saved credentials unreadable.

2. Start n8n:

   ```bash
   make n8n-up
   ```

3. Open <http://127.0.0.1:5678> and create the owner account. Use a strong
   password and your email. Self-hosted n8n has no public sign-up once an
   owner exists.

## The shared secret

The API and n8n share a secret so requests can be HMAC-signed.

1. Generate the secret:

   ```bash
   openssl rand -hex 32
   ```

2. Add it to `api/.env` together with the local n8n URL:

   ```
   N8N_BASE_URL=http://127.0.0.1:5678
   N8N_SHARED_SECRET=<the generated value>
   ```

3. In n8n, create a credential that holds the same value. Use either:
   - *Header Auth*, or
   - a *Custom* credential named `todo-agent-hmac`.

   Workflows read the secret from that credential. Because
   `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` is set in `.env.n8n`, code nodes
   cannot read container environment variables, so the credential is the
   only place the value is available inside workflows.

## LLM provider key

Create an n8n credential for your provider (e.g. *Anthropic* or *OpenAI*)
and use it in the parsing workflow. Never put the key in the repo or in
`api/.env`.

## Import a workflow

1. In the n8n UI, choose **Import from file**.
2. Select `integrations/n8n/workflows/<name>.json`.
3. Open the workflow, attach the credentials from the previous sections
   (`todo-agent-hmac` and the LLM provider), then activate it.

## Export a workflow

Export to the repo so the workflow is version-controlled without
credentials:

```bash
# 1. Export inside the container
docker compose --env-file .env.db --profile n8n exec n8n \
  n8n export:workflow --id=<id> --output=/tmp/w.json

# 2. Copy it out
docker compose --env-file .env.db --profile n8n cp n8n:/tmp/w.json \
  integrations/n8n/workflows/<name>.json
```

**Check the exported JSON for credentials before committing.** The
contract test added in BE-041 fails if any slipped in.

## Backup

Backups are encrypted with `N8N_ENCRYPTION_KEY` and should be kept outside
the repo.

```bash
# Workflows
docker compose --env-file .env.db --profile n8n exec n8n \
  n8n export:workflow --all --backup --output=/tmp/backup/

# Credentials (encrypted with the n8n encryption key)
docker compose --env-file .env.db --profile n8n exec n8n \
  n8n export:credentials --all --output=/tmp/creds.json
```

Copy `/tmp/backup/` and `/tmp/creds.json` out of the container to your
backup location.

## Upgrade

1. Read the n8n release notes.
2. Bump the image tag in `docker-compose.yml`.
3. Back up first (see above).
4. Restart:

   ```bash
   make n8n-down && make n8n-up && make n8n-check
   ```

5. Roll back by restoring the previous tag if anything breaks.

## Troubleshooting

`make n8n-check` prints three lines:

| Line | Meaning | Fix |
|---|---|---|
| `✗ n8n health … run: make n8n-up` | n8n process is not responding | `make n8n-up` |
| `✗ n8n readiness …` | n8n process is up but its database is not reachable | wait, then check `make n8n-logs` |
| `✗ api/.env N8N_BASE_URL …` | API is pointed at the wrong URL | set `N8N_BASE_URL` in `api/.env` to the URL shown |

Other symptoms:

- **"Credentials could not be decrypted"** — `N8N_ENCRYPTION_KEY` in
  `.env.n8n` does not match the key that encrypted the credentials. Restore
  the correct key from your password manager.
- **Login loops / can't stay signed in** — `N8N_SECURE_COOKIE=false` is
  required for plain `http://127.0.0.1`. Do not change this to `true` until
  you serve n8n over HTTPS.
- **Silent failures in workflows** — `make n8n-logs` first, then check that
  both the HMAC credential and the LLM provider credential are attached.

## Licence note

n8n is released under the [Sustainable Use License](https://github.com/n8n-io/n8n/blob/master/LICENSE.md).
Self-hosting for personal, internal use is allowed. Do not resell n8n or
offer it as a service to others.
