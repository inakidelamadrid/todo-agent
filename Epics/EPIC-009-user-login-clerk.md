# EPIC-009: User login with Clerk (infra)

- **Status:** in-tickets
- **Type:** infrastructure (formalizes foundation **F-1 User login**)
- **Owner:** Ignacio
- **Depends on:** none
- **Used by:**
  - EPIC-001 to EPIC-006: every feature screen and its API routes;
  - EPIC-006: step-up re-auth before revealing numbers or downloading (see 5.6);
  - [BE-046](../tickets/backend/BE-046-start-code-pairing.md): Telegram pairing needs a logged-in user.

## 1. Summary

Today nobody logs in. People and machines share one static `X-API-Key`, and the browser only reaches the API because the Vite dev server adds that key to every request (`web/vite.config.ts`). A production build has no way to authenticate at all.

This epic adds a real login for **people**, using [Clerk](https://clerk.com):

1. **Web app:** a sign-in screen when signed out; the app when signed in. Every API call carries a short-lived session token.
2. **API:** one shared dependency accepts either a verified Clerk session (a person) or an API key (a machine), and tells the route which one it got.
3. **Owner only:** the API accepts only my Clerk user ID, whatever Clerk itself allows.

## 2. Goals

- Only I can sign in and use the app.
- A signed-out browser sees a sign-in screen and can reach no data.
- The API knows *who* is calling (`User` or `Machine`), through one dependency, so later epics can require a person for sensitive actions.
- API keys keep working for machines (n8n, scripts, the Telegram webhook's own secret is unchanged).
- Login works in a production build, not only through the dev proxy.
- Token checks are pure functions, tested without calling Clerk.

## 3. Non-goals

- Per-user data ownership (`user_id` columns). The app stays single-owner.
- F-2 Scoped API keys.
- EPIC-001's public, token-gated signing page for the second person.
- Our own magic-link or login emails (Clerk sends its own; EPIC-007's login-link template is not needed for this).
- Choosing production hosting.
- Building passkeys or sessions ourselves.

## 4. Architecture decision

Evaluated on 2026-11-15, after noticing ngrok's auth features.

| Option | How it works | Pros | Cons |
|---|---|---|---|
| **A. ngrok Traffic Policy `oauth`** | ngrok asks for a Google login at the tunnel and lets one email through | Free (3 users), almost no code | Protects only traffic through the tunnel (localhost bypasses it). Identity reaches the API unsigned, so the API must trust by network position. No passkeys or step-up re-auth. An expired session answers `fetch` with a redirect, not a `401`. Ties auth to the tunnel vendor while hosting is undecided |
| **B. Clerk** | Clerk hosts users and sessions; the SPA uses its React SDK; the API verifies a signed session token | Real app-level sessions on any host. Signed tokens. Ready-made sign-in UI. Free tier covers this app | A vendor holds the login. More code on both sides than A. Passkeys and the sign-up allowlist need the paid plan |
| **C. Hand-rolled (`webauthn` + our own sessions)** | We store credentials and sessions | No vendor | The most security-sensitive code to write and review; not worth it for one user |

**Decision (owner): B, Clerk.**

Facts checked on 2026-11-15 (re-check when unfolding; never copy a version from here without looking it up):

- Clerk Hobby plan: free up to 50,000 monthly users. Pro: $25/month, or $20/month billed yearly.
- Passkeys are Pro only. Clerk's allowlist "requires a paid plan for production use". Restricted (invite-only) sign-up mode has no stated plan requirement.
- React SDK: `@clerk/react` 6.18.8 (supports React 19). `@clerk/clerk-react` is deprecated.
- Python: `clerk-backend-api` 7.1.0 (MIT). Its `authenticate_request` takes an `httpx.Request`, so FastAPI needs an adapter. The alternative is `pyjwt` with Clerk's public key.

### Chosen design

**Web app**

- `ClerkProvider` wraps the app in `web/src/main.tsx`, configured with `VITE_CLERK_PUBLISHABLE_KEY`. The publishable key is meant to be public, so it may be in the bundle. The Clerk *secret* key never goes to the frontend.
- `web/src/App.tsx` renders the current app when signed in and a sign-in screen when signed out.
- The shared request helper (planned in FE-002) adds `Authorization: Bearer <session token>`, taken from Clerk's `getToken()` on each call. Tokens are short-lived; Clerk refreshes them.
- The Vite dev proxy stops adding `X-API-Key`. It only forwards `/api/*`.

**API**

- A `Principal` value in code: `User(user_id)` or `Machine(key_label)`, both frozen dataclasses.
- One shared dependency in `api/app/security.py`, beside today's `require_api_key`:
  - valid Clerk session token from the owner → `User`;
  - valid API key → `Machine`;
  - anything else → `401`; a valid token from someone who is not the owner → `403`.
- Routers in `api/app/main.py` switch from `require_api_key` to the new dependency. A second dependency, "must be a `User`", is available for routes a machine may not call.
- Token verification is a **port** (a function type) with a fake for tests and one real adapter:
  - RS256 signature, checked with the Clerk instance's public key from an environment variable, so no network call per request;
  - `exp` and `nbf`;
  - `azp` must be one of our allowed origins;
  - `sub` must be in the owner allowlist from an environment variable.
- The Telegram webhook is unchanged: public, guarded by its secret header.

```
Browser ── Bearer session token ──▶ /api/* ──▶ FastAPI ── verify (pure) ──▶ User
n8n / scripts ── X-API-Key ────────────────▶ FastAPI ── compare ────────▶ Machine
Telegram ── secret header ─────────────────▶ /telegram/webhook (unchanged)
```

## 5. Requirements

### 5.1 Sign-in and sign-out (web)

- **Signed out:** a full-page sign-in screen, styled to match `DESIGN.md` (tokens, type scale, light and dark). Not Clerk's default look.
- **Signed in:** a small account control in the app shell with my name or email and **Sign out**.
- **States to polish:** loading (Clerk still starting: no flash of the app or of the sign-in screen), error (Clerk unreachable), signing out, keyboard focus, phone width.
- **No sign-up link.** Sign-up is closed (5.4).

### 5.2 Session handling (web)

- Every API request carries a fresh token from `getToken()`.
- A `401` from the API means the session ended: show the sign-in screen and a calm toast. Unsaved input is not silently dropped where it can be kept.
- A `403` means "signed in, but not allowed": show a clear message with a sign-out button, not a loop.

### 5.3 Principal and dependency (API)

- `Principal = User | Machine`, immutable.
- Pure function: claims + settings + current time → `User` or a typed rejection reason (`expired`, `not_yet_valid`, `wrong_party`, `not_owner`, `malformed`).
- Shared dependency returns the `Principal`; no route checks headers itself.
- `WWW-Authenticate` on `401`, as today.
- The OpenAPI docs show both schemes (bearer and API key).

### 5.4 Owner allowlist

- `CLERK_ALLOWED_USER_IDS`: comma-separated Clerk user IDs. Empty means the app refuses to start, like `API_KEYS` today.
- Clerk's sign-up mode is set to **Restricted** in its dashboard as a second barrier (human step).
- The API check is the one that counts: it holds even if the Clerk dashboard setting is changed by mistake.

### 5.5 `GET /me`

- Protected; needs a `User`. Returns `{ "userId": "…", "kind": "user" }` in camelCase.
- Used by the web app to confirm the API accepts the session, and by later epics.
- A `Machine` calling it gets `403`.

### 5.6 Step-up re-auth (later slice)

- EPIC-006 wants a fresh confirmation before revealing numbers or downloading.
- Clerk offers re-verification of a session; confirm its plan requirements and API when this slice is unfolded. Passkeys need Pro.
- Not built in the first slice; see open question 3.

### 5.7 Configuration and secrets

- Web: `VITE_CLERK_PUBLISHABLE_KEY` in `web/.env.example`.
- API: `CLERK_JWT_PUBLIC_KEY` (PEM), `CLERK_AUTHORIZED_PARTIES` (allowed origins), `CLERK_ALLOWED_USER_IDS` in `api/.env.example`.
- Nothing hardcoded. Real values are set by the human; agents never read them out or log them.
- Separate Clerk instances for development and production (Clerk provides both).

## 6. Data model (draft)

Nothing in the database. Clerk holds the user and sessions.

| Entity | Key fields |
|---|---|
| `User` (code only) | `user_id` (Clerk `sub`) |
| `Machine` (code only) | `key_label` (which API key; a placeholder until F-2 names keys) |

## 7. Security and privacy

- Every endpoint still requires auth by default. This epic changes *how*, not *whether*.
- The browser never holds an API key again.
- Tokens are verified on every request: signature, expiry, origin (`azp`), owner.
- Every protected route has tests for: no credentials, a wrong API key, an expired token, a token for another origin, a token for a non-owner.
- Tests sign tokens with a key pair generated in the test, never a real Clerk key.
- Tokens, keys and the `Authorization` header never appear in logs.
- Clerk stores my email, name and session history. Nothing from the app's data goes to Clerk.
- CORS stays off while the browser reaches the API on the same origin. If hosting later puts them on different origins, that is its own ticket.

## 8. Epic acceptance criteria

- [ ] A signed-out browser sees the sign-in screen and every `/api/*` call returns `401`.
- [ ] After I sign in, the bills screen works as it does today.
- [ ] A different Clerk account gets `403` from the API.
- [ ] An expired or tampered token gets `401`.
- [ ] A machine with a valid `X-API-Key` still gets through; `GET /me` refuses it with `403`.
- [ ] No API key in the web bundle or added by the dev proxy.
- [ ] A production build of the web app can sign in (calling the API from it waits for the hosting decision).
- [ ] `make api-test` and `make web-test` pass.

## 9. Ticket breakdown

Backend tickets and frontend tickets can run in parallel until FE-013, which needs BE-063. Step-up re-auth (5.6) is deferred to EPIC-006 and has no ticket here.

**Human steps (before the first manual check):** create the Clerk application (development instance), enable Google, set sign-up to **Restricted**, sign in once to create your user, then copy the three API values (BE-058) and the publishable key (FE-009) into the env files.

**Backend**

1. [BE-058](../tickets/backend/BE-058-clerk-settings.md): Clerk settings and parsers. Depends on: none
2. [BE-059](../tickets/backend/BE-059-principal-and-claim-checks.md): `Principal` types and pure claim checks. Depends on: none
3. [BE-060](../tickets/backend/BE-060-token-decoder-port-and-fake.md): Token decoder port, `verify_session`, fake. Depends on: BE-059
4. [BE-061](../tickets/backend/BE-061-rs256-token-decoder-pyjwt.md): RS256 decoder with `pyjwt[crypto]`. Depends on: BE-058, BE-060
5. [BE-062](../tickets/backend/BE-062-require-principal-dependency.md): `require_principal` dependency. Depends on: BE-058, BE-060
6. [BE-063](../tickets/backend/BE-063-switch-routers-to-require-principal.md): Switch routers, refuse to start without Clerk settings. Depends on: BE-061, BE-062
7. [BE-064](../tickets/backend/BE-064-me-endpoint-require-user.md): `GET /me` and `require_user`. Depends on: BE-063

**Frontend**

1. [FE-009](../tickets/frontend/FE-009-install-clerk-provider.md): Install the Clerk SDK, `ClerkProvider`. Depends on: none
2. [FE-010](../tickets/frontend/FE-010-auth-gate.md): `AuthGate` and its four views. Depends on: FE-009
3. [FE-011](../tickets/frontend/FE-011-sign-in-screen.md): Styled sign-in screen. Depends on: FE-010
4. [FE-012](../tickets/frontend/FE-012-bearer-token-in-request.md): Bearer token in the request helper. Depends on: FE-002
5. [FE-013](../tickets/frontend/FE-013-wire-session-token-to-api.md): Send Clerk's token with every API call. Depends on: FE-010, FE-012, BE-063
6. [FE-014](../tickets/frontend/FE-014-account-control-sign-out.md): Account control and sign-out. Depends on: FE-010
7. [FE-015](../tickets/frontend/FE-015-handle-401-session-ended.md): `401` ends the session calmly. Depends on: FE-013
8. [FE-016](../tickets/frontend/FE-016-handle-403-not-allowed-screen.md): `403` not-allowed screen. Depends on: FE-015
9. [FE-017](../tickets/frontend/FE-017-remove-api-key-from-dev-proxy.md): Remove the API key from the Vite dev proxy. Depends on: FE-013

**Later (not ticketed)**

- Step-up re-auth (5.6), with EPIC-006.
- Calling the API from a production build: needs the hosting decision.
- [BE-046](../tickets/backend/BE-046-start-code-pairing.md) (Telegram pairing) now depends on BE-064.

## 10. Open questions (answer in place)

1. Sign-in methods: Google, email code, or both?
   - Answer: Google only. (answered)
2. Pay for Clerk Pro now (passkeys, Clerk-side allowlist), or stay on the free plan?
   - Answer: Stay on the free plan. (assumed)
3. Step-up re-auth: part of this epic, or deferred until EPIC-006 needs it?
   - Answer: Deferred to EPIC-006. (answered)
4. How long may a session last before I must sign in again?
   - Answer: Clerk's default session length. (assumed)
5. Does the second person in EPIC-001 ever get an account, or only signing links?
   - Answer: Signing links only, no account. (assumed)
6. Token verification package: `pyjwt` with Clerk's public key, or Clerk's `clerk-backend-api`? (Check both on PyPI when unfolding.)
   - Answer: `pyjwt[crypto]`. (answered)
7. Keep `/health` and `/ping` public, as today?
   - Answer: Yes, `/health` and `/ping` stay public. (answered)
