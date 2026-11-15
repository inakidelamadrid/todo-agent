# BE-040: Bot setup runbook and command list script

- **Status:** todo
- **Workspace:** backend
- **Epic:** [EPIC-008: Telegram integration](../../Epics/EPIC-008-telegram-integration.md) §5.1, §7
- **Assigned agent / harness / model:**
- **Depends on:** BE-013, BE-039
- **Can run in parallel with:** none
- **Public endpoint?** no
- **Review size:** ~80 lines + runbook, 4 files, ~12 min

## Goal

A runbook walks you through creating the dev and prod bots safely, and one command publishes the command list to Telegram.

## Why this ticket exists

Several steps can only be done by you, in the BotFather chat. Writing them down once, with the security settings, keeps dev and prod consistent and documents token rotation before it is needed.

## Read first

- `RUNBOOK-migrations.md`: tone and format.
- https://core.telegram.org/bots/features#botfather

## Design

- **Pattern:** Documentation plus a thin script over an immutable table.
- **Data flow:** `COMMAND_DESCRIPTIONS` → `make telegram-commands` → `bot.set_my_commands(...)`.

## Packages

None new. Standard library and what is already installed.

## Details

**Files**

- `RUNBOOK-telegram.md` (new, repo root).
- `api/app/telegram/routing.py` (changed): `COMMAND_DESCRIPTIONS: Mapping[str, str]`, the 11 user-facing commands from epic §5.1 with a short description each (`start` is not listed).
- `api/scripts/telegram_webhook.py` (changed): subcommands `commands` and `whoami`. `Makefile`: `telegram-commands`, `telegram-whoami`.
- `api/tests/test_telegram_commands.py` (new).

**Runbook sections**

1. Create two bots with BotFather: `…_dev_bot` and the real one. Never share a token between them.
2. BotFather settings for both: `/setprivacy` → Enabled; `/setjoingroups` → Disabled; name, description, picture.
3. Put the token in `api/.env` (`TELEGRAM_BOT_TOKEN`). Generate `TELEGRAM_WEBHOOK_SECRET` and `TELEGRAM_CALLBACK_SECRET` with the command from `.env.example`.
4. Find your user ID: `make telegram-whoami` (see below), then set `TELEGRAM_ALLOWED_USER_ID`.
5. Start the tunnel: `ngrok http 8000`; run `make telegram-webhook url=…`; check `make telegram-info`.
6. `make telegram-commands`.
7. Rotation: BotFather `/revoke` → new token in `.env` → re-run step 5. Rotate the webhook secret by changing it and re-running step 5.
8. Troubleshooting: silent bot → `make telegram-info`; `401`s in the API log → secret mismatch.

**`whoami`.** Only works while no webhook is registered: calls `getUpdates` once and prints the sender ID of the most recent message, nothing else. It exists so you do not have to give your ID to a third-party bot.

**Human steps.** Steps 1 to 4 are yours. The agent must stop and ask, and must never read, print or log a token.

## Steps

1. Add `COMMAND_DESCRIPTIONS` and its test.
2. Add the two subcommands and targets.
3. Write the runbook.
4. Stop and hand steps 1–4 to the human.

## Tests

- `test_every_described_command_is_routable`: keys ⊆ `COMMANDS`.
- `test_every_epic_command_is_described`: the 11 names.
- `test_descriptions_fit_telegram_limits`: 1–256 characters.
- `test_whoami_prints_only_an_id` (mocked).

## Acceptance criteria

- [ ] The runbook covers creation, privacy settings, secrets, tunnel, commands, rotation and troubleshooting
- [ ] `make telegram-commands` publishes exactly the 11 commands
- [ ] No token or secret appears in the runbook, the scripts' output or the repo
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

Follow the runbook top to bottom with the dev bot. In Telegram, type `/` in the bot chat: the 11 commands appear with descriptions. Then send `/help` (BE-021).

## Review guide

Read the diff in this order, and check:

1. The runbook: would you be able to redo this in six months from it alone?
2. `COMMAND_DESCRIPTIONS`: wording of each description.
3. `whoami`: prints one number.

Things that should *not* be in the diff: prod hosting; pairing.

## Out of scope

- Pairing by `/start <code>` → BE-046.
- n8n setup → BE-041.

## Notes / log

The agent adds progress notes, decisions and open questions here.
