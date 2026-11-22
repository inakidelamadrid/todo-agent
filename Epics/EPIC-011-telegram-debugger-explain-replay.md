# EPIC-011: Telegram debugger: route explainer and replay (infra)

- **Status:** in-tickets
- **Type:** infrastructure (developer tooling)
- **Owner:** Ignacio
- **Split from:** [EPIC-008: Telegram integration](EPIC-008-telegram-integration.md) §5.7 on 2026-11-22, so the first playground slice (update log, template preview, send test message) can ship without it.
- **Depends on:** EPIC-008 inbound pipeline (BE-006 to BE-015) and the playground foundation (BE-065 to BE-069, FE-018 to FE-021)

## 1. Summary

Two playground tools for understanding routing decisions:

- **Route explainer:** take a recorded fixture, or compose an update (text, command, callback, photo with caption), and see each router step in order: allowlist, idempotency, callback → command → pending mode → keyword → default, with the rule that matched. Dry run by default: nothing stored, no handler runs.
- **Run for real (replay):** opt-in and confirmed, it sends the composed update through the same path as the webhook after the secret check (allowlist, idempotency, router, handler), as if it came from the admin's own chat.

All other playground rules from EPIC-008 §5.7 apply unchanged (admin only, off by default, never in production, every action recorded, no content stored).

## 2. Rules

Moved from EPIC-008 §5.7:

- **Dry run by default.** *Run for real* changes something and asks for confirmation.
- *Run for real* uses a playground-only `update_id` range so it can never collide with a real Telegram update, and the resulting records are marked as playground-made.
- **Never a way around the guards.** The explainer does not accept updates on behalf of other users. A composed update is always processed as if it came from the admin's own chat.
- Composed text exists only in the request and is not stored or logged.

## 3. Data model

| Entity | Key fields |
|---|---|
| `RouteExplanation` (response only, not stored) | steps[] (name, verdict, detail), finalRoute |

## 4. Acceptance criteria

- [ ] The route explainer gives the same route as the real router for every recorded fixture, and stores nothing in a dry run.
- [ ] *Run for real* executes the handler once, only for the admin's own chat, and its records are marked as playground-made.
- [ ] Each endpoint has tests for: no credentials (`401`), a signed-in non-admin (`403`), a valid API key (`403`), and the playground switched off (`404`).

## 5. Ticket breakdown

Moved from EPIC-008 (IDs kept), plus FE-030 split out of FE-022.

Backend:

- [BE-072](../tickets/backend/BE-072-compose-update.md): Compose an update: a small form becomes an `InboundUpdate`. Depends on: BE-006
- [BE-073](../tickets/backend/BE-073-explain-route.md): `explain_route`: the router's decision, step by step, as a pure function. Depends on: BE-009, BE-013
- [BE-074](../tickets/backend/BE-074-playground-explain-endpoint.md): `POST /admin/telegram/explain`: dry-run route explanation. Depends on: BE-068, BE-069, BE-072, BE-073
- [BE-075](../tickets/backend/BE-075-extract-process-update.md): Extract `process_update` from the webhook (no behaviour change). Depends on: BE-015
- [BE-076](../tickets/backend/BE-076-playground-replay-endpoint.md): `POST /admin/telegram/replay`: run a composed update for real. Depends on: BE-074, BE-075

Frontend:

- [FE-030](../tickets/frontend/FE-030-playground-client-explain-replay.md): Playground client, part 3: explain and replay. Depends on: FE-021, BE-074, BE-076
- [FE-025](../tickets/frontend/FE-025-route-explainer-panel.md): Route explainer panel: composer form and step list (presentational). Depends on: FE-020
- [FE-026](../tickets/frontend/FE-026-wire-route-explainer-run-for-real.md): Wire the explainer, with the confirmed **Run for real**. Depends on: FE-030, FE-025

## 6. Open questions (answered in EPIC-008, kept here)

1. May the route explainer ever *execute* the handler (a real end-to-end replay), or stay dry run only?
   - Answer: Yes, as an explicit, confirmed *Run for real* mode. Dry run stays the default.
