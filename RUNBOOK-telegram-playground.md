# Telegram Playground Runbook

How to switch on the admin-only Telegram debugger playground (EPIC-008 §5.7)
on your machine, then a short tutorial to try what exists today.

**What exists today:** the admin role, the guarded API probe, the
**Playground** rail entry, the playground screen with its four tabs, and the
**Updates** panel showing **sample data**. The Updates panel isn't wired to
the API yet (FE-021, FE-024), and the Explain, Templates and Test message tabs
say *Coming soon*. None of this needs a Telegram bot or a webhook.

## 1. Prerequisites

You have already done these for the Bills app:

- `api/.env` with the Clerk values (see `RUNBOOK-clerk-setup.md`).
- `web/.env.local` with `VITE_CLERK_PUBLISHABLE_KEY`.
- Docker running.

## 2. Find your Clerk user ID

It is the same value you put in `CLERK_ALLOWED_USER_IDS` (it starts with
`user_`). If you don't have it to hand: Clerk dashboard → **Users** → your
user → **User ID**.

## 3. Switch the playground on

Add or edit these three lines in `api/.env`:

```
ADMIN_USER_IDS=<your Clerk user ID>
APP_ENV=development
TELEGRAM_PLAYGROUND_ENABLED=true
```

- `ADMIN_USER_IDS` is a comma-separated list. Empty means nobody is an admin.
  An admin must also be in `CLERK_ALLOWED_USER_IDS`, or they can't sign in.
- The API **refuses to start** with `TELEGRAM_PLAYGROUND_ENABLED=true` and
  `APP_ENV=production`. That's deliberate: the playground never runs in
  production.

## 4. Start everything

```bash
make db-up         # Postgres and Redis
make api-migrate   # adds the playground_actions table (BE-069)
make api-dev       # API on 127.0.0.1:8000
make web-dev       # web app on 127.0.0.1:5173 (second terminal)
```

Open the web app at the origin listed in `CLERK_AUTHORIZED_PARTIES`
(by default `http://localhost:5173`).

`api-dev` reloads on code changes, not on `.env` changes. **Restart it after
every edit to `api/.env`.**

## 5. Tutorial

### Step 1: you are an admin

1. Sign in with Google.
2. Open DevTools → **Network**, filter by `me`, and reload. You should see
   **one** request to `/api/me`, answering
   `{"userId": "user_…", "kind": "user", "roles": ["admin"]}`.

`roles` is empty for everyone not in `ADMIN_USER_IDS`. The web app reads it
in one place (`isAdmin`), and a failed `/me` never counts as admin.

### Step 2: open the playground

1. A **Playground** entry (flask icon) now sits under **Bills** in the rail.
   On a phone it is in the top bar.
2. Click it. The address ends in `#playground`, and the
   **Telegram playground** screen opens.
3. Press the browser's **Back** button: you are on Bills again. **Forward**
   brings the playground back.

### Step 3: tour the tools

1. Four tabs: **Updates**, **Explain**, **Templates**, **Test message**.
2. Click **Updates**, then use **← / →** to move between tabs and
   **Enter** or **Space** to open one. The focus ring shows where you are.
3. Explain, Templates and Test message say *Coming soon*, each with one line
   on what the tool will do.

### Step 4: read the update log (sample data)

The Updates tab shows six sample updates. Real updates appear once the
webhook (BE-008 to BE-015) and the wiring (FE-021, FE-024) land.

1. Each row shows **when** it arrived, its **kind**, the **route** the router
   chose, and its **status**. Times under an hour are relative ("4 min ago");
   older ones are shown in Mexico City time. Hover a time to see the exact
   timestamp.
2. The `default` text row has a blue **Playground** tag. That marks updates
   made by the playground's *Run for real*, never by Telegram.
3. Set **All statuses → Failed**: only `callback:bills.mark_paid` remains.
4. Back to **All statuses**, then type `command` in **Route**: two rows.
5. Type `zzz`: the panel says *Nothing matches*. Clear the box.
6. No message text appears anywhere, by design: the log stores metadata only.

### Step 5: watch the guards from the API

The page doesn't call the playground API yet (FE-021 will), so call it from
the DevTools **Console** while signed in:

```js
const token = await Clerk.session.getToken()
const r = await fetch('/api/admin/telegram/playground', { headers: { Authorization: `Bearer ${token}` } })
r.status, await r.json()
```

| Change in `api/.env` (then restart `make api-dev`) | Status | Meaning |
|---|---|---|
| Nothing (set up as above) | `200` `{"enabled": true}` | Admin, switch on |
| `TELEGRAM_PLAYGROUND_ENABLED=false` | `404` | Switched off: the endpoint "doesn't exist" |
| Remove your ID from `ADMIN_USER_IDS` | `403` | Signed in, but not an admin |
| Run `fetch` without the header | `401` | No credentials, whether the switch is on or off |

When you remove yourself from `ADMIN_USER_IDS`, also reload the web app.
The **Playground** entry disappears, and typing `#playground` by hand shows
Bills. Hiding the entry is a courtesy; the API check is the one that counts.

Put the three lines back the way section 3 has them when you're done.

### Step 6: look at it on a phone and in the dark

1. DevTools → device toolbar → a 375 px phone. The rail becomes a top bar
   with both entries; the tabs scroll sideways without the page scrolling;
   the update log becomes stacked rows.
2. Switch your OS to dark mode: the whole screen follows.

## 6. Turning it off

Set `TELEGRAM_PLAYGROUND_ENABLED=false` (or delete the line) and restart the
API. The endpoints answer `404`. The rail entry stays visible to admins, and
once FE-021 lands the screen will say *The playground is switched off*.

## 7. What comes next

| Ticket | Adds |
|---|---|
| FE-021 | Real probe: the off, not-an-admin and error states appear on their own |
| FE-024 | The update log reads real updates from `GET /admin/telegram/updates` |
| FE-025, FE-026 | Route explainer, with a confirmed **Run for real** |
| FE-027, FE-028 | Template preview |
| FE-029 | Send a test message to your own chat |
