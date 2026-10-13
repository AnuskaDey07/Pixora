# Pixora — runbook

"What to do when X breaks."

## Container won't start

    docker compose ps                       # which one is unhealthy?
    docker compose logs <service> --tail=100
    docker compose logs <service> --tail=100 --follow

## Port already in use

If Windows has something on :80, edit .env:

    NGINX_HTTP_PORT=8080

Then `make down && make up`. Access via http://localhost:8080.

## API is unhealthy

    docker compose logs api --tail=100

Common causes:
- Postgres not ready — wait_for_db.py retries for 60s.
- Import error in app/__init__.py — Python traceback in logs.
- Command syntax error in docker-compose.yml — "No application module specified".

## Workers not picking up jobs

    docker compose logs worker-light --tail=50
    docker compose logs worker-ml --tail=50
    docker compose exec redis redis-cli -n 1 LLEN light
    docker compose exec redis redis-cli -n 1 LLEN ml
    docker compose exec redis redis-cli -n 1 LLEN gpu

Non-zero lengths mean jobs are queued but not consumed.

## Stuck jobs

A job in running for longer than 2 × soft_time_limit is stuck.

    docker compose exec api python scripts/reconcile_stuck_jobs.py

## Full reset

    make reset     # stops, deletes volumes, restarts fresh

Wipes Postgres, Redis, MinIO, and the frontend build volume.

## Nuclear

    docker compose down -v --remove-orphans
    docker system prune -a --volumes
    make up

Careful: prune -a --volumes removes images and volumes from every project
on this machine, not just Pixora.

## WSL2 quirks

Occasionally the Docker daemon dies after a Windows update:

    # From PowerShell:
    wsl --shutdown

Reopen Ubuntu, then `docker info` to verify.

## Where things live

- Images (upload): MinIO bucket pixora-uploads
- Thumbnails: MinIO bucket pixora-thumbs
- Job results: MinIO bucket pixora-results
- Inpaint masks: MinIO bucket pixora-masks
- Postgres data: Docker volume pixora_postgres_data
- Frontend build: Docker volume pixora_frontend_dist
