# Tickets: backend workspace

This workspace (`todo-agent-backend`) takes **backend tickets only**. Its agent builds the FastAPI service (e.g. in `api/`).

## Routing

| Ticket is about… | Goes to |
|---|---|
| FastAPI endpoints, Python, API keys/security, database, pytest | **this workspace**: `todo-agent-backend/tickets/` |
| React UI, components, styling, Zustand stores, Vite, design | `todo-agent-frontend/tickets/` |
| Both (e.g. a new API plus the screen that uses it) | Split it into two tickets, one per workspace, and link them with `Depends on` |

## Ticket files

- One Markdown file per ticket: `BE-001-short-title.md`, `BE-002-…`, numbered in order.
- Copy [`_template.md`](_template.md) to start one.
- The agent updates `Status` as it works: `todo` → `in-progress` → `review` → `done` (or `blocked`, with the reason).

## Agent rules

- Follow the root `CLAUDE.md`: Python + FastAPI, secure first (every endpoint needs an API key unless a ticket explicitly says it is public), pytest with pytest-xdist, functional style.
- Touch only backend files unless the ticket says otherwise.
- Never commit, push or send anything without asking first.
- The remote `origin` points to the main workspace (`/Users/ignacio/todo-agent`) for merging finished work back.
