# FE-018: Session roles: `/me` client, `isAdmin` and a small store

- **Status:** review (implemented on branch `idelamadrid/FE-023` with FE-018, FE-019, FE-020 and FE-023; approved by the user, PR open)
- **Workspace:** frontend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.7 Debugger playground
- **Assigned agent / harness / model:** Claude Code / claude-opus-5-5
- **Depends on:** BE-067
- **Can run in parallel with:** BE-065 to BE-069
- **Review size:** ~60 lines, 4 files plus tests, ~10 min

## Goal

After sign-in the app loads `/api/me` once and knows whether the user is an admin, through a pure `isAdmin(me)` and a `useSessionStore`.

## Why this ticket exists

The playground entry must be shown only to admins. This adds the knowledge and nothing visible, so the next ticket (the entry and screen switch) is only about navigation. The API still enforces access; this is for not showing a dead link.

## Read first

- `web/src/features/bills/api/client.ts` and `store/useBillsStore.ts`: the client and store style.
- `web/src/lib/api.ts`: `createRequest`.
- `web/src/features/auth/AuthGate.tsx`: where 'signed in' is known.

## Design

- **Pattern:** Pure model function plus a small Zustand store with explicit status.
- **Data flow:** `AuthGate` signed-in → `useSessionStore.load()` → `fetchMe` → `{ me, status }` → `isAdmin(me)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/auth/session.ts` (new): `interface Me { readonly userId: string; readonly kind: 'user'; readonly roles: readonly string[] }`; `isAdmin(me: Me | null): boolean` (pure: `roles` includes `'admin'`); `fetchMe(request): Promise<Me>` calling `GET /me`.
- `web/src/features/auth/useSessionStore.ts` (new): `{ me: Me | null; status: 'idle' | 'loading' | 'ready' | 'error'; load(): Promise<void>; reset(): void }`. `load` is a no-op while loading or ready. On error `me` stays `null` (so nobody is treated as admin by accident).
- `web/src/features/auth/AuthGate.tsx` (changed): call `load()` when the view becomes `signed-in`, `reset()` on sign-out.
- Tests: `session.test.ts`, `useSessionStore.test.ts` (new).

A missing `roles` field in the response is treated as `[]`.

## Steps

1. Model and `isAdmin` with tests.
2. Client and store with tests.
3. Call `load` from the gate.
4. `make web-test`, `make web-build`.

## Tests

- `test_is_admin_true_with_admin_role`.
- `test_is_admin_false_for_null_empty_or_other_roles`.
- `test_fetch_me_parses_roles_and_defaults_to_empty`.
- `test_load_sets_ready_and_me`.
- `test_load_error_leaves_me_null`.
- `test_load_twice_fetches_once`.
- `test_reset_clears_me`.

## Acceptance criteria

- [ ] `/api/me` is requested once after sign-in
- [ ] `isAdmin` is pure and false unless `roles` contains `admin`
- [ ] A failed load never yields an admin
- [ ] Sign-out clears the session store
- [ ] Nothing visible changes
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-test`: green.
2. Sign in: the network panel shows one `/api/me` request.

## Review guide

Read the diff in this order, and check:

1. `session.ts`: is `isAdmin` the only place that reads `roles`?
2. `useSessionStore.ts`: what is `me` after an error?

Things that should *not* be in the diff: Any admin UI, navigation, playground code.

## Out of scope

- The admin-only entry → FE-019.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- `session.ts`: `Me`, pure `isAdmin` (the only reader of `roles`), `toMe` (missing `roles` → `[]`), `fetchMe(request)`.
- `useSessionStore.ts`: `createSessionStore(loadMe)` factory like the bills store; `load` is a no-op while loading or ready; an error leaves `me` null.
- `AuthGate.tsx`: `load()` when the view is `signed-in`, `reset()` when `signed-out`.
- Not checked against a live sign-in here (no `web/.env.local` in this workspace): confirm one `/api/me` request by hand.
