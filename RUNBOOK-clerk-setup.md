# Clerk Setup Runbook

How to configure user login (EPIC-009) with [Clerk](https://clerk.com) after
you create your account. Result: three values in `api/.env` (gitignored —
agents never read, print or log them):

- `CLERK_JWT_PUBLIC_KEY` — verifies session tokens locally (public by design)
- `CLERK_AUTHORIZED_PARTIES` — origins our tokens may come from
- `CLERK_ALLOWED_USER_IDS` — only your Clerk user ID gets in

Do this with the **development instance** only; production is a later decision.

## 1. Create the application

1. Sign up at https://clerk.com and create a new **application**
   (e.g. `todo-agent`). Clerk creates a development instance automatically.
2. When asked for sign-in methods, enable **Google** (adjust if you decided
   otherwise in the epic's open questions).

## 2. Restrict sign-up (only you can ever have an account)

1. Dashboard → **User & authentication** → **Restrictions**
   (paths shift; look for "Sign-up mode" / "Restrictions").
2. Set sign-up to **Restricted** (invitation-only). Nobody can self-register.

## 3. Create your user

1. From the dashboard, **Users** → **Create user** (or open the sign-in URL
   once and accept your own invitation).
2. Sign in with Google once so the account exists.
3. In **Users**, open your user and copy the **User ID** (looks like
   `user_2abc…`).

## 4. Copy the JWT public key

1. Dashboard → **API keys** → **Show JWT public key** → **PEM format**.
2. Paste it in `api/.env` on **one line**, with newlines written as `\n`
   (the backend expands them):

   ```
   CLERK_JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----
   ```

   The public key is public by design, but still keep it out of git.

## 5. Fill the three variables in `api/.env`

```
CLERK_JWT_PUBLIC_KEY=<one-line PEM, as above>
CLERK_AUTHORIZED_PARTIES=http://localhost:5173
CLERK_ALLOWED_USER_IDS=<your user_2… ID>
```

- `CLERK_AUTHORIZED_PARTIES` is the token's `azp` claim: the origin the
  browser app is served from. `http://localhost:5173` is already the value in
  `api/.env.example`; add the production origin later, comma-separated.
- `CLERK_ALLOWED_USER_IDS`: comma-separated; today only your own ID.

## 6. Validate

Prints a boolean only, never any value:

```bash
cd api && uv run python -c \
  "from app.settings import get_settings, clerk_enabled; \
   s = get_settings(); \
   print('clerk_enabled:', clerk_enabled(s))"
```

Expected: `clerk_enabled: True`. If `False`, one of the three variables in
`api/.env` is missing or empty.

## What this runbook does *not* cover

Nothing reads these values yet — the dependency that actually verifies
tokens is BE-062/BE-063, and the web app side starts at FE-009. This runbook
covers the dashboard setup and env values only.
