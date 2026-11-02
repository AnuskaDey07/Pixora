# Pixora — dev commands
SHELL := /bin/bash
DC    := docker compose

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Pixora — make targets:"
	@echo "  up            Start full stack (no GPU)"
	@echo "  up-gpu        Start full stack + GPU worker"
	@echo "  down          Stop everything"
	@echo "  reset         Nuke volumes + restart fresh"
	@echo "  logs          Tail all logs"
	@echo "  logs-api      Tail api logs"
	@echo "  logs-worker   Tail all worker logs"
	@echo "  ps            Show running services"
	@echo "  shell-api     Bash into api container"
	@echo "  shell-db      psql into postgres"
	@echo "  migrate       Run alembic upgrade head"
	@echo "  seed          Seed dev data"
	@echo "  test          Run backend tests"
	@echo "  fe-install    npm install in frontend/"
	@echo "  fe-dev        Run Vite dev server on host (port 5173)"
	@echo "  fe-build      Rebuild frontend image + refresh nginx volume"

.PHONY: up
up:
	$(DC) up -d --build
	@echo "Pixora up → http://localhost  (MinIO console: http://localhost:9001)"

.PHONY: up-gpu
up-gpu:
	$(DC) --profile gpu up -d --build
	@echo "Pixora up with GPU worker"

.PHONY: down
down:
	$(DC) down

.PHONY: reset
reset:
	$(DC) down -v
	$(DC) up -d --build

.PHONY: logs
logs:
	$(DC) logs -f --tail=100

.PHONY: logs-api
logs-api:
	$(DC) logs -f --tail=100 api

.PHONY: logs-worker
logs-worker:
	$(DC) logs -f --tail=100 worker-light worker-ml

.PHONY: ps
ps:
	$(DC) ps

.PHONY: shell-api
shell-api:
	$(DC) exec api bash

.PHONY: shell-db
shell-db:
	$(DC) exec postgres psql -U pixora -d pixora

.PHONY: migrate
migrate:
	$(DC) exec api flask db upgrade

.PHONY: seed
seed:
	$(DC) exec api python scripts/seed.py

.PHONY: test
test:
	$(DC) exec api pytest -q

.PHONY: fe-install
fe-install:
	cd frontend && npm install

.PHONY: fe-dev
fe-dev:
	cd frontend && npm run dev

.PHONY: fe-build
fe-build:
	$(DC) up -d --build frontend
	$(DC) restart nginx
.PHONY: gen-secrets
gen-secrets:
	$(DC) exec -T api python scripts/generate_secrets.py

.PHONY: prod-up
prod-up:
	$(DC) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

.PHONY: prod-down
prod-down:
	$(DC) -f docker-compose.yml -f docker-compose.prod.yml down

.PHONY: backup
backup:
	./scripts/backup.sh

.PHONY: restore
restore:
	@test -n "$(FILE)" || (echo "usage: make restore FILE=backups/pixora-backup-....tar.gz"; exit 1)
	./scripts/restore.sh $(FILE)

.PHONY: backups-list
backups-list:
	@ls -lh backups/ 2>/dev/null || echo "no backups yet — run 'make backup'"

.PHONY: reset-demo
reset-demo:
	@echo "This wipes the database and MinIO, then re-seeds demo data."
	@read -p "Type 'yes' to continue: " c && [ "$$c" = "yes" ]
	$(DC) exec -T api flask db downgrade base
	$(DC) exec -T api flask db upgrade
	$(DC) exec -T api python scripts/seed.py

.PHONY: smoke
smoke:
	$(DC) exec -T api python scripts/smoke_test.py

.PHONY: fe-rebuild
fe-rebuild:
	@echo "Rebuilding frontend (cache-busted, no-cache)..."
	CACHE_BUST=$$(date +%s) $(DC) build --no-cache frontend
	$(DC) down frontend
	docker volume rm pixora_frontend_dist 2>/dev/null || true
	$(DC) up -d frontend
	sleep 3
	$(DC) restart nginx
	@echo "Frontend rebuilt with fresh assets."

.PHONY: help
help:
	@echo "Pixora — make targets:"
	@echo "  up            Start full stack"
	@echo "  up-gpu        Start with GPU worker"
	@echo "  down          Stop everything"
	@echo "  reset         Nuke volumes + restart fresh"
	@echo "  logs          Tail all logs"
	@echo "  logs-api      Tail api logs"
	@echo "  logs-worker   Tail worker logs"
	@echo "  ps            Show running services"
	@echo "  shell-api     Bash into api container"
	@echo "  shell-db      psql into postgres"
	@echo "  migrate       Run alembic upgrade head"
	@echo "  seed          Seed demo data"
	@echo "  smoke         Run end-to-end smoke test"
	@echo "  test          Run pytest"
	@echo "  fe-install    npm install in frontend/"
	@echo "  fe-dev        Run Vite dev server on host"
	@echo "  fe-build      Rebuild frontend image"
	@echo "  fe-rebuild    Full frontend rebuild (no cache, fresh volume)"
	@echo "  gen-secrets   Generate strong secrets for .env.prod"
	@echo "  prod-up       Start in production mode"
	@echo "  prod-down     Stop production stack"
	@echo "  backup        Full backup (Postgres + MinIO)"
	@echo "  restore       Restore from backup: make restore FILE=..."
	@echo "  backups-list  List existing backups"
	@echo "  reset-demo    Wipe DB and re-seed (interactive)"

.PHONY: build-gpu
build-gpu:
	@echo "Building CUDA ML image — only needed on a GPU host."
	@echo "Downloads ~6 GB. Takes ~40 minutes."
	docker compose build --no-cache worker-gpu

.PHONY: gpu-up
gpu-up:
	docker compose --profile gpu up -d --build worker-gpu
