# Pixora — Ownership

Pixora is a 2-person collaboration split cleanly along a single interface.

## The interface

File: backend/app/ml/base.py — frozen.

Everything ML-side is a pure function returning MLResult. Everything web-side
calls those functions from Celery tasks only.

## Web owner (@Ayush26112003)

Owns:

- backend/app/api/ — every Flask endpoint
- backend/app/tasks/ — every Celery task
- backend/app/models/ — every SQLAlchemy model
- backend/app/services/ — storage, imaging, job helpers
- backend/app/__init__.py, config.py, extensions.py
- backend/migrations/ — Alembic
- frontend/ — every Vue component, store, view
- docker-compose.yml, nginx/, Makefile, .github/
- backend/scripts/ — dev tooling
- backend/app/ml/_stub.py — placeholder ML impls

## ML owner (@garaitapasi)

Owns:

- backend/app/ml/* (except base.py and _stub.py)
- notebooks/ — experiments and prototyping
- Model weights under backend/app/ml/models/ (gitignored)

Rules:

- Pure Python. No Flask, no Celery, no DB, no HTTP.
- Input: PIL.Image + params dict. Output: MLResult.
- Models load once at worker startup; never per call.
- Every function documents params/meta in docs/ml-contracts.md.

## Boundary rules

1. ML code never imports from app.api, app.models, app.services, or app.tasks.
2. Web code never imports under app.ml except base and specific model modules inside Celery tasks.
3. No file I/O in ML code. Persistence is the web layer's job.
4. base.py changes require both owners' approval (enforced via CODEOWNERS).

## Change process

- Every change lands via PR.
- Reviewer auto-assigned via .github/CODEOWNERS.
- If a PR crosses the boundary, tag the other owner.
