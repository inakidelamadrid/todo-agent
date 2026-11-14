# todo-agent — Project Rules

## Stack

- **Backend:** Python + FastAPI.
- **Frontend:** React (TypeScript) + shadcn/ui for components, styled with Tailwind CSS. Built and bundled with **Vite**.
- **Backend tests:** pytest, run in parallel with pytest-xdist (`pytest -n auto`) for speed. Use FastAPI's `TestClient` for endpoint tests, and cover the API-key protection on every protected route.

## Code style: functional programming

Applies to the whole codebase: frontend controllers, models, and backend.

- Prefer pure functions; keep side effects (I/O, DB, network, state) at the edges.
- Favor immutability: no mutating inputs or shared state; return new values.
- Compose small, single-purpose functions instead of classes and inheritance.
- Frontend: function components and hooks only; no class components.
- Backend: plain functions for routes, services, and logic; use immutable data models (e.g. frozen Pydantic models / dataclasses).

## Backend: secure first

- Security comes first in every backend decision.
- **Every endpoint requires an API key by default.** An endpoint is public only when I explicitly say to make it public.
- Enforce the API key via a shared FastAPI dependency, not ad-hoc checks per route.
- Never hardcode keys; load them from environment variables.

## Design: premium everywhere

- Everything user-facing must look **premium**: refined, polished, intentional — never default or templated.
- Typography: a deliberate type scale, generous line-height, a quality font pairing (no browser defaults).
- Spacing: generous whitespace, consistent spacing scale, clear visual hierarchy.
- Color: restrained palette with one accent; define colors as tokens; support light and dark mode.
- Details: subtle shadows, soft radii, smooth transitions and micro-interactions, crisp icons.
- Polish every state: hover, focus, active, loading, empty, error.
- Responsive and accessible: works at phone width, good contrast, keyboard-friendly.

## Communication

- Keep responses **shorter than usual**: lead with the result, skip filler and long recaps.

## Never send without asking

- **Never send, post, publish, share, email, message, push, or deploy anything without asking first** and getting an explicit yes.
- This includes git pushes, PRs, artifacts, messages, and any upload to an external service.
- Approval covers only that one action; ask again for the next.
