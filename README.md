# Pixora

**AI-powered image creation and editing platform.**

Pixora is a unified web platform for image generation, editing, detection, and
search — replacing the need to juggle eight different tools for eight different
image tasks.

> **Status:** Batches 1–5 complete. Every mandatory feature is wired
> end-to-end. ML integrations drop in as the ML teammate's models land.

---

## What it does

Mandatory features (all implemented):

| # | Feature | Queue | Endpoint |
|---|---|---|---|
| 1 | Text-to-image generation | `gpu` | `POST /api/jobs` type `generate` |
| 2 | Resizing and rescaling | `light` | `POST /api/jobs` type `resize` |
| 3 | NSFW / vulgar content handling | `ml` | auto on upload + `/api/admin/nsfw-queue` |
| 4 | AI-generated image detection | `ml` | `POST /api/jobs` type `detect_ai` |
| 5 | Sketch-guided generation (ControlNet) | `gpu` | `POST /api/jobs` type `controlnet` |
| 6 | Image format conversion | `light` | `POST /api/jobs` type `convert` |
| 7 | Background removal and replacement | `ml` | `POST /api/jobs` type `remove_bg` |
| 8 | Generative fill / object eraser | `gpu` | `POST /api/jobs` type `inpaint` |
| 9 | Object detection | `ml` | `POST /api/jobs` type `detect_objects` |
| 10 | Image-to-image generation | `gpu` | `POST /api/jobs` type `img2img` |

Should-have:

- Semantic search over image library (CLIP + pgvector) — implemented
- Reverse image search (visual similarity) — implemented

---

## Architecture

Nine services, three Celery queues, one frozen interface between web and ML.

| Layer | Service | Role |
|---|---|---|
| Frontend | `frontend` + `nginx` | Vue 3 SPA, served static |
| API | `api` (Flask + Gunicorn) | HTTP endpoints, enqueues jobs |
| Queue | `redis` | Celery broker + result backend |
| Workers | `worker-light` | Pillow ops (resize, convert, thumb) |
| Workers | `worker-ml` | CPU models (NSFW, objects, CLIP) |
| Workers | `worker-gpu` | Diffusion (generate, inpaint, ControlNet) |
| Scheduler | `worker-beat` | Periodic maintenance (stuck-job reconcile) |
| DB | `postgres` + pgvector | Metadata + embeddings |
| Storage | `minio` | 4 buckets: uploads, thumbs, results, masks |

Every feature follows one flow:

1. Upload via Vue → `POST /api/images/upload`
2. Flask stores in MinIO, inserts into `images` table
3. User triggers action → `POST /api/jobs` → job row + Celery task
4. Worker picks up task, calls ML function, gets `MLResult`
5. Result uploaded to MinIO, job row updated to `done`
6. Vue polls `GET /api/jobs/:id` and renders the result

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

Step 4 — run migrations:

    make migrate

Step 5 — (first time only) create an admin account:

    docker compose exec api python scripts/create_admin.py you@example.com --create --password yourpassword

Then visit:

- App: http://localhost
- MinIO console: http://localhost:9001 (login `pixora` / `pixora_dev_minio`)
- API health: http://localhost/api/health

First `make up` builds images and takes 4–8 minutes. Subsequent runs are seconds.

---

## Verification

    make smoke

Runs a 40-assertion end-to-end test:

- health, auth (register/login/refresh/change-password), 401s
- image upload, validate, list, get, delete, pagination
- all 11 job types fired and polled to completion
- search (semantic, similar, empty-query rejection)
- admin (users, jobs, NSFW queue)
- MinIO round-trip

If all pass, the platform is healthy.

---

## Dev commands

    make up          # start the full stack
    make up-gpu      # start with GPU worker (uses stub tasks on CPU)
    make down        # stop everything
    make reset       # stop + delete volumes + restart fresh
    make logs        # tail all logs
    make logs-api    # tail api logs
    make logs-worker # tail worker logs
    make shell-api   # bash into the API container
    make shell-db    # psql into Postgres
    make migrate     # run alembic migrations
    make seed        # seed dev data
    make smoke       # run the end-to-end smoke test
    make test        # run pytest

---

## Repository layout

    backend/
      app/
        api/         Flask blueprints
        models/      SQLAlchemy models
        services/    business logic (storage, imaging, jobs, security)
        tasks/       Celery tasks
        ml/          ML code — owned by ML teammate
      migrations/    Alembic
      scripts/       dev tooling (wait_for_db, init_minio, create_admin, smoke_test)
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

- **Ayush** (`@Ayush26112003`) — full-stack web: API, Celery, DB, storage,
  frontend, deployment.
- **Tapasi** (`@garaitapasi`) — ML/DL: every model and inference pipeline in
  `backend/app/ml/`.

The boundary between them is a single frozen interface:
`backend/app/ml/base.py`. See `docs/ownership.md`.

---

## License

MIT — see `LICENSE`.

New to the project? Read [docs/onboarding.md](docs/onboarding.md) for a step-by-step setup guide with OS-specific instructions and troubleshooting.
