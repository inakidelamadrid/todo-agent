# Tickets

Work is split by side. Each side has its own folder, numbering and agent workspace.

| Folder | Prefix | Agent works in | Covers |
|---|---|---|---|
| [`frontend/`](frontend/) | `FE-` | `todo-agent-frontend` (`web/`) | React UI, shadcn/ui + Tailwind, Zustand, Vite, Vitest, design (impeccable, DESIGN.md) |
| [`backend/`](backend/) | `BE-` | `todo-agent-backend` (`api/`, Docker, `Makefile`) | FastAPI, Python, API keys, Postgres/Redis, pytest |

- If a feature needs both sides, write one ticket in each folder and link them with `Depends on`.
- Each folder has its own `README.md` (rules) and `_template.md`.
- An agent reads and updates tickets only in its own folder.
- Shared rules and the domain model live in the root `CLAUDE.md`.

## Priority

Every ticket carries a `Priority` field, 5 (highest) to 1 (lowest):

| Priority | Meaning |
|---|---|
| **5** | Very important — next in line |
| **4** | Important — schedule soon |
| **3** | Normal — the default |
| **2** | Low — pick up when idle |
| **1** | Can hold until further decision |

Priority is set or changed only by the user, never by the agent.
