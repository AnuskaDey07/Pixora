# Pixora

**AI-powered image creating and editing platform.**

Pixora is a unified web platform for image generation, editing, detection, and search — replacing the need to juggle eight different tools for eight different image tasks.

> **Status:** Batch 1 complete — infrastructure boots end-to-end.
> Active development.

---

## What it does

| # | Feature | Queue |
|---|---|---|
| 1 | Text-to-image generation | gpu |
| 2 | Resizing and rescaling | light |
| 3 | NSFW / vulgar content handling | ml |
| 4 | AI-generated image detection | ml |
| 5 | Sketch-guided generation (ControlNet Scribble) | gpu |
| 6 | Image format conversion | light |
| 7 | Background removal and replacement | ml |
| 8 | Generative fill and object eraser (inpainting) | gpu |
| 9 | Object detection | ml |
| 10 | Image-to-image generation | gpu |

Should-have:

- Semantic search over the image library (CLIP + pgvector)
- Reverse image search (visual similarity)

---

## Architecture

Nine services, three Celery queues, one interface between web and ML.

| Layer | Service | Role |
|---|---|---|
| Frontend | `frontend` + `nginx` | Vue 3 SPA, served static |
| API | `api` (Flask + Gunicorn) | HTTP endpoints, enqueues jobs |
| Queue | `redis` | Celery broker + result backend |
| Workers | `worker-light` | Pillow ops (resize, convert, thumb) |
| Workers | `worker-ml` | CPU models (NSFW, YOLO, CLIP) |
| Workers | `worker-gpu` | Diffusion (SD, ControlNet, inpaint) |
| DB | `postgres` + pgvector | Metadata + embeddings |
| Storage | `minio` | 4 buckets: uploads, thumbs, results, masks |

Every feature follows one flow:

1. Upload via Vue → POST /api/images/upload
2. Flask stores in MinIO, inserts into images table
3. User triggers action → POST /api/jobs → job row + Celery task
4. Worker picks up task, calls ML function, gets MLResult
5. Result uploaded to MinIO, job row updated to done
6. Vue polls GET /api/jobs/:id and renders the result
---

## Quickstart

Prerequisites: Docker Engine (WSL2 or native Linux), `make`, `git`.

Step 1 — clone:

    git clone git@github.com:AnuskaDey07/Pixora.git
    cd Pixora

Step 2 — create your env file:

    cp .env.example .env

Step 3 — boot the stack:

    make up

Then visit:

- App: http://localhost
- MinIO console: http://localhost:9001 (login pixora / pixora_dev_minio)
- API health: http://localhost/api/health

First `make up` builds images and takes 4–8 minutes. Subsequent runs are seconds.

---

## Dev commands

    make up          # start the full stack (no GPU)
    make up-gpu      # start with GPU worker (requires nvidia runtime)
    make down        # stop everything
    make reset       # stop + delete volumes + restart fresh
    make logs        # tail all logs
    make logs-api    # tail api logs
    make shell-api   # bash into the API container
    make shell-db    # psql into Postgres
    make migrate     # run alembic migrations
    make seed        # seed dev data
    make test        # run pytest
    ---

## Repository layout

    backend/
      app/
        api/         Flask blueprints
        models/      SQLAlchemy models
        services/    business logic (storage, imaging, jobs)
        tasks/       Celery tasks
        ml/          ML code — owned by ML teammate
      migrations/    Alembic
      scripts/       dev tooling
      tests/         pytest
    frontend/
      src/
        api/         axios clients
        stores/      Pinia state
        composables/ reusable hooks
        views/       routed pages
        components/  reusable UI
    nginx/           reverse proxy config
    docs/            contracts, ownership, runbook

---

## Team & ownership

- Ayush (`@Ayush26112003`) — full-stack web: API, Celery, DB, storage, frontend, deployment.
- Tapasi (`@garaitapasi`) — ML/DL: every model and inference pipeline in backend/app/ml/.

The boundary between them is a single frozen interface: backend/app/ml/base.py. See docs/ownership.md.

---

## License

MIT — see LICENSE.