# Choosing packages

Reuse beats writing. Less hand-written code means less for the human to review, and a well-used package has already met the edge cases. But every dependency is also something to trust and maintain, so each new one must be justified and verified in the ticket that adds it.

## Order of preference

1. **Already installed.** Check `web/package.json` and `api/pyproject.toml` first, and the standard library / platform (`Intl`, `crypto`, `zoneinfo`, `datetime`, `hmac`, `secrets`).
2. **Already in the ecosystem we use.** A shadcn/ui component (`npx shadcn add …`), a FastAPI / Pydantic / SQLAlchemy feature, a Zustand middleware.
3. **A well-established package** that passes the checks below.
4. **Hand-written**, only for small, domain-specific logic (bill due rules, radar priority) or when a package would be heavier than twenty clear lines.

Don't hand-write: date and timezone maths, recurrence rules, form state and validation, schema parsing, retries and backoff, HTTP clients, signature and JWT handling, password or token hashing, queues and schedulers, file-type detection, virtualised lists, drag and drop, charts.

## Checks before recommending a new package

Run these when writing the ticket and put the results in its Packages table. Registry lookups are read-only and send nothing about this project. Do not install anything while unfolding.

```bash
npm view <pkg> version license time.modified repository.url
```

```bash
curl -s https://api.npmjs.org/downloads/point/last-week/<pkg>
```

```bash
curl -s https://pypi.org/pypi/<pkg>/json | python3 -c "import json,sys; i=json.load(sys.stdin)['info']; print(i['version'], i.get('license_expression') or i.get('license'), i['requires_python'], i['project_urls'])"
```

A package qualifies when:

- It has had a release in roughly the last year and its repository is active.
- It is widely used (npm: on the order of 100k+ weekly downloads; PyPI: a recognised project, ideally used or recommended by FastAPI / Pydantic / SQLAlchemy docs).
- Its licence is permissive (MIT, BSD, Apache-2.0, ISC).
- It ships types (TypeScript types bundled or `@types/…`; Python type hints).
- It supports our versions: React 19, Vite, Python ≥ 3.12, async SQLAlchemy 2.
- It fits the functional style (functions and hooks, not class hierarchies to extend).
- It doesn't duplicate something installed. Two libraries for one job needs a stated reason.
- Its own dependencies don't conflict with ours. Read `requires_dist` (PyPI) or `peerDependencies` (npm) and compare with what is installed or already ticketed; a package that pins a shared dependency to an old major fails this check.
- Its registry page carries no "maintenance only", "deprecated" or "unmaintained" notice. Search the description for those words.

If the checks can't be run, say so in the ticket and make "verify the package against the registry" its first step, rather than asserting facts from memory. Never write a version number you haven't just looked up.

## In the ticket

- One new dependency per ticket at most. Introduce it in the smallest ticket that uses it, so the reviewer meets the library in isolation.
- State: what it is used for, why it over the alternatives (name one or two), version / licence / last release / downloads, and the exact install command (`npm --prefix web install <pkg>`, `uv add <pkg>` in `api/`).
- Link the one docs page the reviewer should read.
- Security-sensitive packages (auth, crypto, anything parsing untrusted input) get an extra line on why they are trustworthy and how they are configured safely.

## Candidates by need

Starting points, not decisions. They reflect common choices at the time of writing; the registry checks above decide.

**Frontend (npm)**

| Need | Look at |
|---|---|
| UI primitives | shadcn/ui components first (already set up, on Base UI) |
| Icons, toasts, state | `lucide-react`, `sonner`, `zustand` (installed) |
| Schema parsing / API response validation | `zod` or `valibot` |
| Forms | `react-hook-form` with its schema resolver |
| Dates | `date-fns` (pure functions), `Intl.DateTimeFormat` for display |
| Server state, if the hand-rolled store stops scaling | `@tanstack/react-query` (a deliberate change; FE-001 chose Zustand only) |
| Routing, when a second screen arrives | `react-router` or `@tanstack/react-router` |
| Component tests | `@testing-library/react`, `@testing-library/user-event`, `msw` for API mocking |
| Functional helpers | native array methods first; `remeda` if a pipeline needs it |

**Backend (PyPI)**

| Need | Look at |
|---|---|
| Validation, settings | `pydantic`, `pydantic-settings` (installed) |
| DB, migrations | `sqlalchemy`, `asyncpg`, `alembic` (installed) |
| HTTP client | `httpx` (installed for tests; promote to a runtime dependency when needed) |
| Retries | `tenacity` |
| Background jobs / scheduler on Redis | `arq`, or `apscheduler` for simple schedules |
| Redis | `redis` (asyncio client) |
| Recurrence, date maths | `python-dateutil`; `zoneinfo` from the standard library for timezones |
| Signatures, tokens | `hmac` / `secrets` (standard library), `pyjwt`, `itsdangerous` |
| Passkeys / WebAuthn | `webauthn` |
| Google APIs | `google-api-python-client`, `google-auth` |
| Email | a provider's official SDK, or `aiosmtplib` for SMTP |
| Rate limiting | `slowapi` |
| Structured logging | `structlog` |
| Test data, time, property tests | `polyfactory`, `time-machine`, `hypothesis` |
