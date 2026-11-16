# FE-009: Install the Clerk React SDK and add `ClerkProvider`

- **Status:** todo
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §4 Chosen design (Web app), §5.7 Configuration and secrets
- **Assigned agent / harness / model:**
- **Depends on:** none
- **Can run in parallel with:** BE-058 to BE-064
- **Review size:** ~45 lines, 4 files plus tests, ~10 min

## Goal

The app is wrapped in `ClerkProvider`, configured from `VITE_CLERK_PUBLISHABLE_KEY`; a missing or wrong key shows a clear message instead of a blank page. Nothing else about the app changes.

## Why this ticket exists

One new dependency, introduced alone so the reviewer meets Clerk's SDK in isolation. The gate (FE-010) and the sign-in screen (FE-011) build on a provider that already works.

## Read first

- `web/src/main.tsx`: the whole entry file (it is short).
- `web/.env.example`: how dev variables are documented.
- Clerk React quickstart: https://clerk.com/docs/references/react/overview and https://clerk.com/docs/quickstarts/react (check the current prop names before coding).

## Design

- **Pattern:** Provider at the edge, plus a pure config reader (`readPublishableKey`) so the one rule that matters (never accept a secret key) is tested.
- **Data flow:** `import.meta.env` → `readPublishableKey` → `ClerkProvider publishableKey` or `MissingConfigScreen`.

## Packages

| Package | New? | Used for | Why this one |
|---|---|---|---|
| `@clerk/react` 6.18.8 | **new** | Clerk's React SDK: provider, hooks, components | MIT, modified 2026-11-14, about 4.5M downloads last week, bundled types, peer React `~19.3` matches our 19.3.x. `@clerk/clerk-react` is the deprecated name. Alternatives: hand-rolled sessions (rejected in the epic) |

## Details

**Install:** `npm --prefix web install @clerk/react`. Re-run `npm view @clerk/react version license time.modified peerDependencies` first and use what it prints. Docs for the reviewer: https://clerk.com/docs/references/react/overview.

**Security note:** the *publishable* key (`pk_test_…`, `pk_live_…`) is meant to be in the bundle. A *secret* key (`sk_…`) must never reach the frontend, so the reader refuses it and the message never prints the value.

**Files**

- `web/src/lib/clerkConfig.ts` (new): `readPublishableKey(env: { readonly VITE_CLERK_PUBLISHABLE_KEY?: unknown }): string | null` (pure). Returns the trimmed value only when it is a string starting with `pk_test_` or `pk_live_`; anything else (undefined, blank, `sk_…`, other text) → `null`.
- `web/src/main.tsx` (changed): `const key = readPublishableKey(import.meta.env)`; when non-null render `<ClerkProvider publishableKey={key} afterSignOutUrl="/">` around `<App />`; when null render `<MissingConfigScreen />` instead.
- `web/src/features/auth/MissingConfigScreen.tsx` (new): a centered message, "Sign-in is not configured", with the variable name and "copy `web/.env.example` to `web/.env.local`". Uses existing tokens (text, muted text, background); readable in light and dark at phone width.
- `web/src/vite-env.d.ts` (changed or new): declares `VITE_CLERK_PUBLISHABLE_KEY` on `ImportMetaEnv`.
- `web/.env.example` (changed): `VITE_CLERK_PUBLISHABLE_KEY=` with a comment pointing to the Clerk dashboard → API keys → Publishable key.

**Human step:** create the Clerk application if you have not (see BE-058), and put the publishable key in `web/.env.local`. The key is for the development instance only.

## Steps

1. Run the registry check and install the package.
2. Write `readPublishableKey` and its tests, red first.
3. Add the provider and the missing-config screen to `main.tsx`.
4. Run `make web-test` and `make web-build`.

## Tests

- `test_reads_a_test_key`, `test_reads_a_live_key`, `test_trims_whitespace`.
- `test_undefined_blank_and_non_string_are_null`.
- `test_secret_key_is_refused`: `sk_test_abc` → `null`.
- `test_other_text_is_refused`: `hello` → `null`.

## Acceptance criteria

- [ ] `@clerk/react` is installed with `npm install` and its version matches the registry check
- [ ] With a valid key in `web/.env.local` the app renders exactly as before
- [ ] With the key missing or a secret key, the missing-config message shows and the value is never printed
- [ ] `web/.env.example` documents the variable
- [ ] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-dev` with the key set: the bills screen loads; the browser console shows no Clerk error.
2. Remove the key and reload: the 'Sign-in is not configured' screen shows.
3. Put `sk_test_x` there: same screen, and the value is nowhere on the page.

## Review guide

Read the diff in this order, and check:

1. `web/src/lib/clerkConfig.ts`: is the secret-key refusal real and tested?
2. `web/src/main.tsx`: is the provider the only change to the tree?
3. `web/package.json`: exactly one new dependency.

Things that should *not* be in the diff: Any sign-in UI, `useAuth`, a gate, token handling, the Clerk secret key anywhere.

## Out of scope

- Loading, signed-out and signed-in states → FE-010.
- The styled sign-in screen → FE-011.

## Notes / log

The agent adds progress notes, decisions and open questions here.
