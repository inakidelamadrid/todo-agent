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
