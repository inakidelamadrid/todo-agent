# Tickets: frontend workspace

This workspace (`todo-agent-frontend`) takes **frontend tickets only**. Its agent works in `web/`.

## Routing

| Ticket is about… | Goes to |
|---|---|
| React UI, components, styling (shadcn/ui + Tailwind), Zustand stores, Vite, Vitest, design (impeccable, DESIGN.md) | **this folder**: `tickets/frontend/` |
| FastAPI endpoints, Python, API keys/security, database, pytest | `tickets/backend/` (worked in `todo-agent-backend`) |
| Both (e.g. a new API plus the screen that uses it) | Split it into two tickets, one per workspace, and link them with `Depends on` |

## Ticket files

- One Markdown file per ticket: `FE-001-short-title.md`, `FE-002-…`, numbered in order.
- Copy [`_template.md`](_template.md) to start one.
- The agent updates `Status` as it works: `todo` → `in-progress` → `review` → `done` (or `blocked`, with the reason).

## Agent rules

- Follow the root `CLAUDE.md`: TypeScript React, shadcn/ui + Tailwind, Vite, Zustand, functional style, premium design.
- Touch only frontend files unless the ticket says otherwise.
- Never commit, push or send anything without asking first.
- The remote `origin` points to the main workspace (`/Users/ignacio/todo-agent`) for merging finished work back.
