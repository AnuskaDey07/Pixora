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