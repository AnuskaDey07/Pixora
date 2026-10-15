# Pixora — Demo Walkthrough

A script for the final-year defense. Follow it top to bottom, or pick
sections. Total time: ~15 minutes.

---

## Before the demo (5 min setup)

### 1. Start the stack

    cd ~/projects/pixora
    make up            # or: make prod-up for production mode
    docker compose ps  # wait until all containers are healthy

### 2. Seed demo data (first time only, or after a reset)

    make seed

Creates:

- `demo-admin@example.com` / `demo-password-123` (admin)
- `demo-alice@example.com` / `demo-password-123` (user)
- `demo-bob@example.com` / `demo-password-123` (user)
- 6 generated sample images
- ~30 completed jobs (resize, convert, NSFW, embed, background removal)

### 3. Open the browser

    http://localhost

Also have these ready in a terminal:

    make logs             # all logs
    docker compose ps     # status
    curl http://localhost/api/health

### 4. (Optional) Public URL

    cloudflared tunnel --url http://localhost:80

Gives you an HTTPS URL you can open on any device — useful if you're
demoing away from your laptop.

---

## The demo (15 minutes)

### Part 1 — Introduction (1 min)

Say:

> "Pixora is a unified web platform for image generation, editing,
> detection, and search. It replaces the need to juggle eight different
> tools for eight different image tasks. Two-person team: I own the full
> web layer — Flask API, Celery workers, PostgreSQL, MinIO, Vue frontend.
> My teammate owns every ML model."

---

### Part 2 — Login and architecture (2 min)

1. Open http://localhost
2. Log in as `demo-admin@example.com` / `demo-password-123`
3. Land on the Gallery

Say while showing:

> "Nine Docker services: nginx, Flask API, three Celery workers for
> light/ml/gpu queues, a Beat scheduler, PostgreSQL with pgvector,
> Redis, MinIO object storage. Everything is containerized. One
> `make up` starts the whole stack."

Show the terminal:

    docker compose ps

> "All healthy. The API is behind nginx, which also serves the Vue
> build. Every image operation is asynchronous — uploads trigger
> Celery jobs, results land in MinIO, the browser polls for status."

---

### Part 3 — Upload and auto-pipelines (2 min)

1. Click **Upload** in the nav
2. Drag any image onto the drop zone (drag-and-drop works)

Say:

> "On upload, the platform validates the image, generates a thumbnail,
> stores the original in MinIO, and immediately fires two background
> pipelines: NSFW detection and CLIP embedding for search. That happens
> automatically — the user doesn't have to ask for it."

Point at **Recent jobs** at the bottom of the Gallery:

> "Two jobs per upload: `detect_nsfw` and `embed`, both done. The
> NSFW result writes back to the image row; the embedding enables
> semantic search."

---

### Part 4 — The Editor (3 min)

1. Click **Edit** on any image
2. In the sidebar, walk through the tool groups: **Basic**, **Edit**,
   **Generate**, **Detect**, **Search**
3. Pick **Resize** → set 512×512 → click **Run** → result appears
4. Pick **Remove background** → click **Run** → the result panel shows
   a processed version (currently a stub — this is where the ML
   teammate's real model plugs in)
5. Pick **Text to image** → type a prompt → **Run** → placeholder image

Say:

> "Every tool follows the same pattern. The user picks a tool, sets
> params, the frontend creates a job, a worker picks it up, and the
> result comes back. The interface between web and ML is a single
> frozen Python contract — `MLResult`. When my teammate's real models
> land, I swap one import line per task and nothing else changes."

---

### Part 5 — Search (2 min)

1. Click **Search** in the nav
2. Type a query like "mountains" or "sunset" → **Search**
3. Show results

Say:

> "Search is semantic, not filename-based. Every image is embedded with
> CLIP on upload, stored as a 512-dimension vector in pgvector. Search
> encodes the query the same way and finds nearest neighbors. Same for
> 'find similar' — image-to-image similarity."

If the demo has enough images: click **Similar** on an image card and
show the ranked results.

---

### Part 6 — Admin supervision (1 min)

1. Click **NSFW Queue** in the nav
2. Show that flagged images would appear here with Approve/Reject

Say:

> "Moderation is a first-class concern. Every uploaded image is scored
> for NSFW content. Anything above the threshold lands in this admin
> queue. Admins can approve (clears the flag) or reject (deletes the
> image and its MinIO objects). The role model is a `role` enum —
> `user` or `admin` — not a boolean, so future roles like `guest` or
> `power_user` are a schema addition, not a migration."

---

### Part 7 — Reliability (1 min)

Show the terminal:

    docker compose exec -T api python scripts/smoke_test.py

Say while it runs:

> "A 50-assertion end-to-end smoke test. Every endpoint, every job
> type, every error case. Runs in about a minute. This is what we run
> before every deployment."

The test passes → `PASS: 50+ FAIL: 0`.

Show backups:

    ./scripts/backup.sh
    ls -lh backups/

> "One command produces a timestamped archive: Postgres dump, MinIO
> volume, manifest. Restore is the reverse."

---

### Part 8 — Deployment (2 min)

Optionally, open the Cloudflare URL on a phone or a second device:

> "The platform runs locally but deploys to a public HTTPS URL through
> Cloudflare Tunnel — no server, no port forwarding. It could equally
> run on a $5 VPS; the deployment docs cover both paths. Same Docker
> Compose files, same code."

---

## Closing slide

Points to hit in the wrap-up:

1. **Working system** — not a prototype. Every mandatory feature has a
   UI, an endpoint, a task, and a passing test.
2. **Real architecture** — 9 services, 3 queues, a frozen ML interface,
   migrations, backups, deployment docs.
3. **Clean boundary** — web and ML split along one file; the project
   scaled to a 2-person team without blocking.
4. **Verification** — a smoke test proves every layer end-to-end.

---

## Fallback plan if the live demo breaks

Things to have ready:

1. **A backup archive.** If the DB corrupts mid-demo:
       ./scripts/restore.sh backups/pixora-backup-YYYYMMDD-HHMMSS.tar.gz

2. **Screenshots.** Have `docs/screenshots/` ready with images of the
   gallery, editor, search, admin queue, and the smoke test output.
   Switch to screenshots and keep talking.

3. **A copy of this doc.** Read from it if you lose your place.

4. **A backup user.** If `demo-admin@example.com` won't log in (e.g. the
   password was changed accidentally), register a fresh user at
   `/register` — takes 5 seconds.

---

## Things not to do

- Don't run `make reset` during the demo — it wipes all volumes.
- Don't run `flask db downgrade` — it drops tables.
- Don't restart `docker compose down -v` for any reason.
- Don't fake numbers. If a feature isn't working, say "this is the
  stub, real model lands at integration time." Honest is stronger.

---

## Q&A preparation

Expected questions and short answers:

**"Why Flask and not Django?"**
> We only need an API. Flask gives us structure control; Django would
> add admin/template machinery we don't use.

**"How do you scale this?"**
> Every worker is independently scalable. Add more `worker-gpu`
> replicas for heavy models, more `worker-light` for throughput. The
> queues isolate failure domains.

**"What's your biggest risk?"**
> Integration of real ML models. We mitigated it by freezing the
> interface in Week 1 and building the entire web pipeline against
> stubs. Every model drop-in is a single import line.

**"How do you know it works?"**
> `make smoke` — a 50-assertion end-to-end test. It runs in CI, on the
> demo machine, and after every deployment.

**"What about security?"**
> JWT with access + refresh tokens, bcrypt password hashing, rate
> limiting on auth endpoints shared through Redis, role-based access
> with admin-only blueprints, no DB or object storage exposed in
> production, HTTPS via Cloudflare.

**"How would you add a new feature?"**
> Three layers: an ML function in `backend/app/ml/` matching the
> frozen contract, a Celery task wrapping it, and a UI control. Every
> existing feature follows this shape.

**"What's the future work?"**
> Real ML models (in progress by teammate), guest access with reduced
> capability, batch processing, image upscaling, style transfer.
