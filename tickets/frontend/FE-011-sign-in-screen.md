# FE-011: The styled sign-in screen (Google only, no sign-up link)

- **Status:** done
- **Workspace:** frontend
- **Epic:** [EPIC-009: User login with Clerk](../../Epics/EPIC-009-user-login-clerk.md) §5.1 Sign-in and sign-out, §3 Non-goals (no sign-up)
- **Assigned agent / harness / model:** Claude Code / claude-fable-5-2
- **Depends on:** FE-010
- **Can run in parallel with:** BE-058 to BE-064
- **Review size:** ~90 lines, 3 files plus tests, ~15 min

## Goal

Signed-out visitors see a full-page screen in the app's own look, with Clerk's Google sign-in inside it, and no sign-up link.

## Why this ticket exists

Clerk's default look would break the 'premium everywhere' rule. Clerk's `<SignIn>` component handles the OAuth redirect and its edge cases, so we restyle it with its `appearance` option rather than rebuilding the flow, which keeps this ticket small.

## Read first

- `DESIGN.md`: Colors, Typography, Components → Buttons and Cards, Motion, Do's and Don'ts.
- `web/src/index.css`: the token names (`--rail`, `--accent`, and so on) and the `label-caps` utility.
- `web/src/components/AppShell.tsx`: `BrandMark`.
- Clerk appearance prop: https://clerk.com/docs/customization/overview. Check in the docs that CSS variables can be used as `variables` values and how to hide the footer link in the installed version.

## Design

- **Pattern:** Presentational component plus a pure style object (`clerkAppearance`) built only from token references, so 'no hard-coded colours' is testable.
- **Data flow:** `AuthGate` (signed-out) → `SignInScreen` → `<SignIn appearance={clerkAppearance}>`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `web/src/features/auth/clerkAppearance.ts` (new): `export const clerkAppearance` with `variables` mapped to the design tokens as `var(--…)` references (never hex), and `elements` that hide Clerk's footer (the 'Don't have an account? Sign up' link), flatten its card shadow so our card shows, and set the radius from the token.
- `web/src/features/auth/SignInScreen.tsx` (new): full-height layout, brand mark and `todo-agent` wordmark in `label-caps`, one headline and one short line of calm text ('Private to its owner. Sign in to continue.'), then `<SignIn routing="hash" appearance={clerkAppearance} />`. Centered on a single column; on phone width it fills the width with the page gutter.
- `web/src/features/auth/AuthGate.tsx` (changed): the `signed-out` view renders `SignInScreen` instead of the placeholder.
- `web/src/features/auth/clerkAppearance.test.ts` (new).

**States to polish:** loading (Clerk's own skeleton inside the card, no layout jump), error (Clerk shows sign-in errors in place; check they are readable), hover and focus of the Google button, light and dark, phone width, reduced motion.

**No sign-up link anywhere.** The API allowlist (BE-063) is what keeps others out; this removes the invitation.

## Steps

1. Write `clerkAppearance` and its test.
2. Build `SignInScreen`, wire it into `AuthGate`.
3. Check the screen in the browser at both widths and both themes.

## Tests

- `test_appearance_uses_only_token_references`: every colour value is a `var(--…)` string, no `#` or `rgb(`.
- `test_appearance_hides_the_footer_link`: the footer element is hidden.

## Acceptance criteria

- [x] The signed-out screen uses the design tokens and `label-caps`, with Clerk's default look not visible
- [ ] Google sign-in works end to end for the owner in the development instance
- [x] No 'Sign up' link is visible
- [x] Light and dark both look right; phone width has no horizontal scroll; keyboard focus is visible
- [x] Tests pass and the build passes
- [x] Tests pass (`make web-test`) and the build passes (`make web-build`)
- [x] The diff stays within the review size above, or the ticket was split

## How to verify by hand

1. `make web-dev`, signed out: the screen matches `DESIGN.md`. Toggle the OS dark mode: it follows.
2. Resize to 375 px wide: no horizontal scroll.
3. Tab through the screen: the focus ring is visible on the Google button.
4. Click **Continue with Google** and sign in as the owner: the bills screen shows.

## Review guide

Read the diff in this order, and check:

1. `clerkAppearance.ts`: is every value a token reference?
2. `SignInScreen.tsx`: is the layout simple, and does it hold up at 375 px?
3. Compare the screen against `DESIGN.md`'s Do's and Don'ts.

Things that should *not* be in the diff: The account control, sign-out, token handling, any `API_KEY` change.

## Out of scope

- Account control and sign-out → FE-014.
- A custom (non-Clerk) sign-in flow → not planned.

## Assumptions

- Clerk's `appearance` accepts CSS variables and can hide the footer, as its docs indicate. If not, use plain colour values read from the computed tokens and say so in the Notes.

## Notes / log

The agent adds progress notes, decisions and open questions here.

- Branch `idelamadrid/FE-011`, stacked on `idelamadrid/FE-010` (started before FE-010 merged, at the user's request).
- The assumption holds: `appearance.variables` accepts `var(--…)` and `elements.footer: { display: "none" }` hides the sign-up link. Clerk's docs advise plain colour values for older browsers; token references are kept as the ticket asks.
- `appearance` is typed `any` in `@clerk/react` 6.18.8 (the types live in `@clerk/ui`, not installed), so element names were confirmed in the DOM, not by the compiler.
- Clerk's own header is hidden too, since the screen carries the headline.
- Clerk draws the Google button's border as a box-shadow ring and forces `border-width: 0`, so the outline is a box-shadow applied only when not focus-visible; Clerk's focus ring is untouched.
- `fontFamily` is left to inherit: `--font-sans` is not emitted as a runtime variable; `--font-display` is.
- `make web-test` → 52 passed (2 new); `make web-build` passes.
- Checked in Chrome: dark and light (`data-theme`), keyboard focus ring on the Google button, no "Sign up" text in the page, no horizontal scroll at 375 px (in an iframe).
- Not checked: Google sign-in end to end (needs the owner's account), Clerk's in-place sign-in errors, reduced motion.
