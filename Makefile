# Database tooling for local development: Postgres + Redis via Docker Compose.
# Credentials live in .env.db (gitignored); recipes never print them.

.DEFAULT_GOAL := help
ENV_FILE := .env.db
N8N_ENV_FILE := .env.n8n
COMPOSE  := docker compose --env-file $(ENV_FILE)

.PHONY: help check-env check-n8n-env db-up db-down db-restart db-status db-logs db-psql db-redis-cli db-backup db-reset api-migrate api-revision api-test api-dev n8n-up n8n-down n8n-status n8n-logs n8n-check telegram-check telegram-webhook telegram-info telegram-bot-cleanup clerk-key-check clerk-key-fix web-dev web-test web-build

help: ## List available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
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
# The Vite dev proxy only forwards /api/* to the API; the browser authenticates
# with its Clerk session token.

web-dev: ## Start the web app on 127.0.0.1:5173 (needs web/.env.local)
	@test -f web/.env.local || test -f web/.env || { \
		echo "✗ web/.env.local not found (web/.env also works; both are gitignored)."; \
		echo "  Run: cp web/.env.example web/.env.local  — then set VITE_CLERK_PUBLISHABLE_KEY (Clerk dashboard → API keys)."; \
		exit 1; }
	@cd web && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort

web-test: ## Run the frontend tests (Vitest)
	@cd web && npm test

web-build: ## Type-check and build the frontend
	@cd web && npm run build

# --- n8n (local brain-dump parser) -------------------------------------------
# Requires .env.n8n (gitignored). Recipes never print the encryption key.

check-n8n-env: # Internal guard: .env.n8n must exist with a real encryption key
	@test -f $(N8N_ENV_FILE) || { \
		echo "✗ $(N8N_ENV_FILE) not found."; \
		echo "  Run: cp .env.n8n.example .env.n8n — then set N8N_ENCRYPTION_KEY (no 'change-me')."; \
		exit 1; }
	@key=$$(grep -E '^N8N_ENCRYPTION_KEY=' $(N8N_ENV_FILE) | cut -d= -f2); \
	if [ -z "$$key" ]; then \
		echo "✗ N8N_ENCRYPTION_KEY in $(N8N_ENV_FILE) is empty."; \
		exit 1; \
	elif [ "$$key" = "change-me" ]; then \
		echo "✗ N8N_ENCRYPTION_KEY in $(N8N_ENV_FILE) is still 'change-me'. Replace it with a real key."; \
		exit 1; \
	elif [ $$(printf '%s' "$$key" | wc -c) -lt 32 ]; then \
		echo "✗ N8N_ENCRYPTION_KEY in $(N8N_ENV_FILE) is shorter than 32 characters."; \
		exit 1; \
	fi

n8n-up: check-env check-n8n-env ## Start n8n, wait until healthy
	@$(COMPOSE) --profile n8n up -d --wait n8n
	@n8n_port=$$(grep -E '^N8N_PORT=' $(N8N_ENV_FILE) 2>/dev/null | cut -d= -f2); \
	n8n_url="http://127.0.0.1:$${n8n_port:-5678}"; \
	echo "✓ n8n is up: $$n8n_url"

n8n-down: ## Stop the n8n container (data is kept)
	@$(COMPOSE) --profile n8n stop n8n

n8n-status: ## Show n8n container and health
	@$(COMPOSE) --profile n8n ps n8n

n8n-logs: ## Follow n8n logs
	@$(COMPOSE) --profile n8n logs -f n8n

n8n-check: ## Check n8n health/readiness and API wiring
	@status=0; \
	n8n_port=$$(grep -E '^N8N_PORT=' $(N8N_ENV_FILE) 2>/dev/null | cut -d= -f2); \
	n8n_port=$${n8n_port:-5678}; \
	n8n_url="http://127.0.0.1:$${n8n_port}"; \
	health=$$(curl -s -o /dev/null -w '%{http_code}' "$${n8n_url}/healthz" 2>/dev/null || echo "000"); \
	if [ "$$health" = "200" ]; then \
		echo "✓ n8n health      $${n8n_url}/healthz"; \
	else \
		echo "✗ n8n health      $${n8n_url}/healthz   run: make n8n-up"; \
		status=1; \
	fi; \
	ready=$$(curl -s -o /dev/null -w '%{http_code}' "$${n8n_url}/healthz/readiness" 2>/dev/null || echo "000"); \
	if [ "$$ready" = "200" ]; then \
		echo "✓ n8n readiness   $${n8n_url}/healthz/readiness"; \
	else \
		echo "✗ n8n readiness   $${n8n_url}/healthz/readiness   run: make n8n-up"; \
		status=1; \
	fi; \
	api_env="api/.env"; \
	base=$$(grep -E '^N8N_BASE_URL=' "$$api_env" 2>/dev/null | cut -d= -f2-); \
	if [ -z "$$base" ]; then \
		echo "✗ api/.env        N8N_BASE_URL is not set in api/.env"; \
		status=1; \
	elif [ "$$base" = "$${n8n_url}" ]; then \
		echo "✓ api/.env        N8N_BASE_URL points at $${n8n_url}"; \
	else \
		echo "✗ api/.env        N8N_BASE_URL is $$base, expected $${n8n_url}"; \
		status=1; \
	fi; \
	exit $$status

