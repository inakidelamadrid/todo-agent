# FE-001: Wire the bills view to the API

- **Status:** review (implemented on branch `idelamadrid/FE-001-wire-bills-view-to-api`; not committed, awaiting user approval)
- **Workspace:** frontend
- **Assigned agent / harness / model:** Claude Code / desktop app / Claude Opus 5.5
- **Depends on:** BE-003 (bills and payments API, merged to `main`)

## Goal

The bills view reads and writes bills and payments through the FastAPI backend instead of `localStorage`. Everything that works today keeps working, and every API call is protected by `X-API-Key` **without the key ever reaching the browser**.

**Out of scope:**
- Production deployment and auth for real users.
- Server-side totals (the frontend keeps computing occurrences and totals with `schedule.ts`).
- AI planning.
- Any visual redesign: keep the Midnight Transit design in `DESIGN.md`.

## Starting point

Pull `main` first and branch from it. `main` now contains `api/`.

- **Frontend:** `web/src/features/bills/`.
  - `model/` holds the pure functions (`schedule.ts`, `transitions.ts`) and the types.
  - `store/useBillsStore.ts` is a Zustand store with `persist` (localStorage key `todo-agent.bills`), seeded from `data/seed.ts`.
  - `useBillsViewStore` holds the view state (month, focused line).
  - IDs are created client-side with `crypto.randomUUID()`.
- **API:** see `CLAUDE.md` → "Domain model: bills & payments" and `api/README.md`. JSON is camelCase and matches `types.ts`, with these differences:
  - `Bill` also has `createdAt` / `updatedAt`.
  - `id` is created **by the server**.
  - Payments are fetched **per month**: `GET /payments?month=YYYY-MM`.

| Method | Path | Use |
|---|---|---|
| `GET` | `/bills` | Load all bills |
| `POST` | `/bills` | Add bill → `201` + `Bill` |
| `PATCH` | `/bills/{id}` | Edit bill |
| `DELETE` | `/bills/{id}` | Delete bill (its payments cascade) |
| `GET` | `/payments?month=YYYY-MM` | Payments for the shown month |
| `PUT` | `/bills/{id}/payments/{period}` | Mark paid `{actualCents, paidAt}` (idempotent upsert) |
| `DELETE` | `/bills/{id}/payments/{period}` | Undo paid (idempotent) |

- **Run the backend:** `make db-up`, then `make api-migrate`, then `make api-dev` (serves on `127.0.0.1:8000`).

## Details

### Keep the API key out of the browser (Vite dev proxy)

- In `vite.config.ts`, proxy `/api/*` to `API_URL` (default `http://127.0.0.1:8000`), strip the `/api` prefix, and **add the `X-API-Key` header in the proxy**. Read the key with `loadEnv(mode, cwd, '')` from a **non-`VITE_`** variable `API_KEY`.
- The browser only ever calls same-origin `/api/...`, so no CORS change is needed in the API.
- `API_KEY` must **never** appear in client code, the built bundle, logs or `import.meta.env`. Verify by grepping `web/dist` after `npm run build`.
- Add `web/.env.example` with placeholders (`API_URL=http://127.0.0.1:8000`, `API_KEY=change-me`). The real file is `web/.env.local`, which `*.local` in `.gitignore` already ignores.

### Human-in-the-middle

Before running the app against the API, **stop and tell the human**:
1. Create `web/.env.local` (`cp web/.env.example web/.env.local`).
2. Set `API_KEY` to one of the keys in `api/.env` → `API_KEYS`.

Then wait for confirmation. Never generate, read out or log the key. If the proxy starts with no key, or with `change-me`, it should fail with a clear message pointing to `web/.env.local`.

### API client (side effects at the edge)

- `features/bills/api/client.ts`: small typed functions, one per endpoint, built on a single `request()` helper.
  - The helper parses JSON and turns non-2xx responses into a typed `ApiError` carrying `status`, `detail` and, for `422`, the field errors mapped from camelCase `loc` names.
  - No classes beyond the error type.
- Keep pure mapping and merge helpers separate and unit-testable. For example, `mergeMonthPayments(payments, month, fetched)` replaces only that month's entries.

### State (Zustand, no new data-fetching library)

- Replace `persist` and the seed with **async actions** in `useBillsStore`: `loadBills()`, `loadMonth(month)`, `addBill`, `updateBill`, `removeBill`, `markPaid`, `undoPaid`.
- Keep request status in the store: `idle | loading | ready | error`, separately for bills and for each loaded month.
- **Optimistic updates** for mark paid, undo, edit and delete: apply the existing pure transition immediately, call the API, and on failure **roll back** and show an error toast. `addBill` waits for the server, because the server creates the id.
- Loading a month (initial load, month switch) fetches its payments once and caches them. Re-fetch after mutations only if needed.
- `useBillsViewStore` stays as is.
- Delete `data/seed.ts` and the sample-data copy ("Sample bills included…") from the rail and the mobile header. Change the rail note to say bills are saved to the API.

### Existing browser data (no silent loss)

On first load, check for the old `localStorage` key `todo-agent.bills` with bills in it **and** the API returning zero bills. If both are true, show a quiet inline banner:

> Import N bills saved in this browser?

with **Import** and **Discard** buttons.
- **Import** creates the bills through the API, then marks their payments paid, mapping old ids to the new server ids.
- Either choice removes the old key.
- Never import automatically.

### States (premium, per DESIGN.md)

- **Loading:**
  - Skeletons for the currency strip, the network panel and the table, in the existing panel style.
  - No spinner in the middle of content.
- **API unreachable or 5xx:**
  - An inline error panel saying what failed, with a **Retry** button.
  - The rail status shows a scarlet dot with "API offline".
- **401:** a message saying the API key in `web/.env.local` is missing or wrong. Never show the key.
- **Mutations:**
  - Disable the triggering button while it runs.
  - The toast keeps the **Undo** action for mark paid and delete, and Undo calls the API.
- **`422` from the add/edit sheet:** show the server's field errors inline on the matching fields.

### `make` targets

Add these to the root `Makefile`:

| Target | Does |
|---|---|
| `make web-dev` | Start Vite on `5173`; requires `web/.env.local` |
| `make web-test` | Run Vitest |
| `make web-build` | Type-check and build |

## Tests (Vitest)

- **API client** with mocked `fetch`:
  - correct method, path and body for each endpoint;
  - camelCase passes through unchanged;
  - `ApiError` mapping for 401, 404, 422 (field errors) and network failure.
- **Store actions** with a mocked client:
  - optimistic mark paid, then rollback on failure;
  - delete, then rollback;
  - `loadMonth` caching;
  - `mergeMonthPayments` only touches the requested month.
- **Import mapping:** old ids → new ids, payments carried over.
- The existing 17 model tests keep passing.

## Acceptance criteria

- [ ] With the API running, the view loads bills and the shown month's payments from the API. Switching months fetches that month's payments.
- [ ] Add, edit, delete, mark paid (with a different actual amount) and undo all persist across a full page reload and a `make api-dev` restart.
- [ ] Optimistic actions roll back with an error toast when the API fails. Test this by stopping the API mid-session.
- [ ] Loading skeletons, the API-offline error with Retry, the 401 message and inline `422` field errors all look right in **light and dark**, at **desktop (1440) and mobile (390)**, checked in Chrome.
- [ ] The import banner appears only when old browser data exists and the API has no bills. Import and Discard both work and remove the old key.
- [ ] `API_KEY` is absent from `web/dist`, client code and the network requests the browser makes. Only the proxy adds the header.
- [ ] No sample/seed data remains, and nothing says "Saved in this browser".
- [ ] `make web-test` and `make web-build` pass. `impeccable detect` reports no new findings.
- [ ] **Final handoff:** tell the human the exact steps to run everything (`make db-up`, `make api-migrate`, `make api-dev`, `make web-dev`) and where the key goes.
- [ ] Nothing is committed or pushed without asking the user first.

## Notes / log

The agent adds progress notes, decisions and open questions here. Never log keys or passwords.

- **Proxy:**
  - `vite.config.ts` proxies `/api/*` to `API_URL` and adds `X-API-Key` from a non-`VITE_` `API_KEY` read with `loadEnv`.
  - Startup fails if `API_KEY` is missing.
  - **Deviation (user decision):** the local backend uses the `change-me` placeholder, so the proxy only *warns* on `change-me` instead of failing. Change both sides before sharing.
  - `make web-dev` accepts `web/.env.local` or `web/.env` (both gitignored); the human chose `web/.env`.
- **Key never in the browser:**
  - The production bundle has no key value and no `X-API-Key` (checked with grep).
  - The bundle only contains help text naming the `API_KEY` variable.
- **Client:**
  - `features/bills/api/client.ts`: one `request()` helper and typed functions per endpoint.
  - `ApiError` carries `status`, `message` and `fieldErrors`. 422 `loc` names map to camelCase field errors, and network failures become status 0.
  - `toBill` strips the server timestamps.
- **Store:**
  - The Zustand `createBillsStore(api)` factory replaces `persist` and the seed (`data/seed.ts` deleted).
  - It adds `billsStatus`, `loadError`, and a per-month `months` status cache.
  - Mark paid, undo, edit and delete are optimistic and roll back on failure. Add waits for the server-assigned id.
  - Delete's Undo re-creates the bill (new id) and its payments.
- **Pure helpers:** `model/sync.ts` has `mergeMonthPayments`, `parseLegacy` and `planImport`.
- **Import:**
  - The banner appears only when the old `todo-agent.bills` key has bills **and** the API has none.
  - Import and Discard both remove the key.
  - Verified live: 11 bills and their payments imported, and the key was cleared.
- **States:**
  - Skeleton for the strip, network and table.
  - `LoadErrorPanel` has copy for offline (status 0 / 5xx) and for 401, plus Retry.
  - The rail shows "API offline" or "Key rejected".
  - Sheet: Saving… state, 422 field errors inline, and client-side length limits (name ≤80, note ≤200) with friendly copy.
- **Make targets:** `web-dev`, `web-test` and `web-build`.
- **Tests:** 40 pass, including 23 new ones for the client, store and helpers. `npm run build` passes, and `impeccable detect` reports `[]`.
- **Verified in Chrome against the running API:**
  - Import.
  - Mark paid with a different amount (MXN 512.30), which persists across a reload.
  - Undo with requests forced to fail: it rolls back, with an error toast.
  - Month switch with requests failing: the offline panel appears, and Retry recovers.
  - The 422 name error shows inline.
  - Captures at desktop (light) and mobile (light and dark) look right.
- **Not verified live:** the 401 screen (unit-tested only), and the delete + Undo round trip (unit-tested only).
