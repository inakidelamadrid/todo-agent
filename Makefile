# Database tooling for local development: Postgres + Redis via Docker Compose.
# Credentials live in .env.db (gitignored); recipes never print them.

.DEFAULT_GOAL := help
ENV_FILE := .env.db
COMPOSE  := docker compose --env-file $(ENV_FILE)

.PHONY: help check-env db-up db-down db-restart db-status db-logs db-psql db-redis-cli db-backup db-reset api-migrate api-revision api-test api-dev telegram-check telegram-webhook telegram-info telegram-bot-cleanup clerk-key-check clerk-key-fix web-dev web-test web-build

help: ## List available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

check-env: # Internal guard: .env.db must exist and have real passwords
	@test -f $(ENV_FILE) || { \
		echo "✗ $(ENV_FILE) not found."; \
		echo "  Run: cp .env.db.example .env.db  — then set both passwords (no 'change-me')."; \
		exit 1; }
	@! grep -qE '^POSTGRES_PASSWORD=change-me[[:space:]]*$$' $(ENV_FILE) || { \
		echo "✗ POSTGRES_PASSWORD in $(ENV_FILE) is still 'change-me'. Choose a real password."; \
		exit 1; }
	@! grep -qE '^REDIS_PASSWORD=change-me[[:space:]]*$$' $(ENV_FILE) || { \
		echo "✗ REDIS_PASSWORD in $(ENV_FILE) is still 'change-me'. Choose a real password."; \
		exit 1; }
	@! grep -qE '^POSTGRES_PASSWORD=[[:space:]]*$$' $(ENV_FILE) || { \
		echo "✗ POSTGRES_PASSWORD in $(ENV_FILE) is empty."; exit 1; }
	@! grep -qE '^REDIS_PASSWORD=[[:space:]]*$$' $(ENV_FILE) || { \
		echo "✗ REDIS_PASSWORD in $(ENV_FILE) is empty."; exit 1; }

db-up: check-env ## Start Postgres and Redis, wait until healthy
	@$(COMPOSE) up -d --wait
	@echo "✓ Databases are up and healthy. Try: make db-status"

db-down: ## Stop and remove the containers (data is kept)
	@$(COMPOSE) down

db-restart: db-down db-up ## Stop, then start both databases again

db-status: check-env ## Show containers and health
	@$(COMPOSE) ps

db-logs: check-env ## Follow logs for both services, or one with s=postgres / s=redis
	@$(COMPOSE) logs -f $(s)

db-psql: check-env ## Open a psql shell in the Postgres container
	@$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-redis-cli: check-env ## Open an authenticated redis-cli in the Redis container
	@$(COMPOSE) exec redis sh -c 'REDISCLI_AUTH="$$REDIS_PASSWORD" redis-cli'

db-backup: check-env ## Dump Postgres to backups/<timestamp>.sql
	@mkdir -p backups
	@$(COMPOSE) exec -T postgres sh -c 'pg_dump -U "$$POSTGRES_USER" "$$POSTGRES_DB"' \
		> backups/$$(date +%Y%m%d-%H%M%S).sql
	@echo "✓ Backup written to backups/ (latest: $$(ls -t backups | head -1))"

db-reset: check-env ## Destructive: remove containers AND volumes (asks for confirmation)
	@read -p "Type 'reset' to delete all database data: " answer; \
	if [ "$$answer" = "reset" ]; then \
		$(COMPOSE) down -v; \
		echo "✗ All database data deleted."; \
	else \
		echo "Aborted — nothing was deleted."; \
	fi

check-db-running: check-env # Internal: Postgres must be up
	@$(COMPOSE) ps --status running --services 2>/dev/null | grep -q '^postgres$$' || { \
		echo "✗ Postgres is not running — run: make db-up"; exit 1; }

api-migrate: check-db-running ## Run alembic upgrade head (requires make db-up)
	@output=$$(cd api && uv run alembic upgrade head 2>&1); status=$$?; \
	printf '%s\n' "$$output"; test $$status -eq 0 || exit $$status; \
	printf '%s' "$$output" | grep -q 'Running upgrade' || echo "✓ Migrations up-to-date"

api-revision: check-db-running ## Autogenerate an Alembic revision: make api-revision m="message"
	@test -n "$(m)" || { echo 'Usage: make api-revision m="message"'; exit 1; }
	@cd api && uv run alembic revision --autogenerate -m "$(m)"

api-test: ## Run the API test suite in parallel
	@cd api && uv run pytest -n auto

api-dev: ## Start uvicorn with reload on 127.0.0.1:8000
	@cd api && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

telegram-check: ## Print whether Telegram is fully configured; prints a boolean, never a secret
	@cd api && uv run python -c \
		"from app.settings import get_settings, telegram_enabled; \
		s = get_settings(); \
		print('telegram_enabled:', telegram_enabled(s))"

# Alias with a literal colon (needs the \: escape — a plain telegram:check
# target would parse as "target telegram, prerequisite check").
telegram\:check: telegram-check

telegram-webhook: ## Register the dev webhook: make telegram-webhook url=https://<id>.ngrok.app
	@test -n "$(url)" || { echo "usage: make telegram-webhook url=https://<id>.ngrok.app"; exit 1; }
	@cd api && uv run python -m scripts.telegram_webhook set --url "$(url)"

telegram-info: ## Show webhook status (no secrets)
	@cd api && uv run python -m scripts.telegram_webhook info

telegram-bot-cleanup: ## Unregister the webhook (idempotent; run when the tunnel closes)
	@cd api && uv run python -m scripts.telegram_webhook delete

clerk-key-check: ## Validate CLERK_JWT_PUBLIC_KEY in api/.env (message only, nothing echoed wrongly)
	@cd api && uv run python -m scripts.clerk_jwks check

clerk-key-fix: ## Print a paste-ready one-line CLERK_JWT_PUBLIC_KEY=... (never edits .env)
	@cd api && uv run python -m scripts.clerk_jwks fix
# --- Frontend (web/) ---------------------------------------------------------
# The Vite dev proxy adds X-API-Key from web/.env.local (gitignored); the key
# never reaches the browser bundle.

web-dev: ## Start the web app on 127.0.0.1:5173 (needs web/.env.local)
	@test -f web/.env.local || test -f web/.env || { \
		echo "✗ web/.env.local not found (web/.env also works; both are gitignored)."; \
		echo "  Run: cp web/.env.example web/.env.local  — then set API_KEY to one of the keys in api/.env (API_KEYS)."; \
		exit 1; }
	@cd web && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort

web-test: ## Run the frontend tests (Vitest)
	@cd web && npm test

web-build: ## Type-check and build the frontend
	@cd web && npm run build
