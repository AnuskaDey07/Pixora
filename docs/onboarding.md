# Pixora — Developer Onboarding

Welcome. This gets you from zero to a running Pixora stack on your machine in about 30 minutes. Pick the section for your OS, follow it top to bottom, and you'll have every feature working locally.

---

## What Pixora is

A web platform for image generation, editing, detection, and search. Two-person team:

- **Ayush** — full-stack web (Flask, Celery, Postgres, MinIO, Vue, Docker)
- **Tapasi** — all ML/DL models (`backend/app/ml/`)

Every ML feature runs through a Celery task that calls a Python function in `backend/app/ml/`. Right now those functions are **stubs** that return placeholder output — the entire platform works end-to-end without any real model.

Your job: replace stubs with real models, one at a time.

---

## Prerequisites — pick your OS

### If you're on Windows (10 or 11)

You need **WSL2** (Windows Subsystem for Linux) and **Docker Engine inside WSL2**.

**A. Enable WSL2** (in PowerShell as Administrator):

    wsl --install -d Ubuntu

Restart when prompted. Open the Ubuntu app from the Start menu and set a Linux username + password.

**B. Install Docker Engine inside WSL2** (in the Ubuntu terminal):

    sudo apt update && sudo apt upgrade -y
    sudo apt install -y ca-certificates curl gnupg lsb-release make git

    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

**C. Add yourself to the docker group:**

    sudo usermod -aG docker $USER

Close the Ubuntu window completely, reopen it. Verify:

    docker --version
    docker run --rm hello-world

If `hello-world` prints the success message, you're done.

### If you're on macOS

Install **Docker Desktop for Mac** from https://www.docker.com/products/docker-desktop. Open it, wait for the whale icon to stop animating. Verify in Terminal:

    docker --version
    docker run --rm hello-world

### If you're on native Linux (Ubuntu/Debian)

Same as the WSL2 Docker Engine install above, minus the WSL steps. Add `make` and `git` if you don't have them:

    sudo apt install -y make git

Add yourself to the docker group:

    sudo usermod -aG docker $USER

Log out and back in. Verify:

    docker --version
    docker run --rm hello-world

---

## Get the repo

    cd ~
    mkdir -p projects && cd projects
    git clone git@github.com:AnuskaDey07/Pixora.git
    cd Pixora

If you don't have SSH set up on GitHub, use HTTPS instead:

    git clone https://github.com/AnuskaDey07/Pixora.git

---

## First run

    cp .env.example .env
    make up

**The first `make up` takes 4–8 minutes.** It downloads base images (Node, Python, Postgres, Redis, MinIO, nginx), builds the backend, and builds the frontend. Subsequent runs are seconds.

When it finishes, you'll see:

    Pixora up → http://localhost  (MinIO console: http://localhost:9001)

**Apply database migrations:**

    make migrate

**Create an admin user + demo data:**

    make seed

The seed script creates three demo users:

    demo-admin@example.com  /  demo-password-123  (admin)
    demo-alice@example.com  /  demo-password-123
    demo-bob@example.com    /  demo-password-123

---

## Verify it works

Open `http://localhost` in your browser.

1. Log in as `demo-admin@example.com` / `demo-password-123`
2. **Gallery** — see the demo images
3. **Editor** — pick "Remove background" or "Detect NSFW", click Run, wait for the result
4. **Search** — type any word, see semantic results
5. **Upload** — drag any PNG/JPEG; it auto-runs NSFW detection + embedding

If all five work, your environment is correct.

---

## Running the smoke test

    make smoke

That runs ~50 assertions through every endpoint and job type. If it prints `PASS: 50+ FAIL: 0`, the platform is healthy.

Run this before every PR.

---

## Common commands

    make up          # start the stack
    make down        # stop
    make logs        # tail all logs
    make logs-api    # tail api logs
    make shell-api   # bash into the api container
    make shell-db    # psql into Postgres
    make migrate     # run DB migrations
    make seed        # populate demo data
    make smoke       # run end-to-end test
    make reset-demo  # wipe DB and re-seed (careful)
    make fe-rebuild  # rebuild frontend with fresh cache

---

## Troubleshooting

### `make: command not found`

    sudo apt install -y make

### `docker: command not found` in WSL

Your WSL integration with Docker isn't on. If you installed Docker Engine natively inside WSL (as above), this shouldn't happen. If you used Docker Desktop on Windows, open its Settings → Resources → WSL Integration → enable your distro.

### `Cannot connect to the Docker daemon`

    sudo systemctl start docker
    sudo systemctl enable docker

Then try again.

### A container is `Restarting` on loop

    docker compose logs <service> --tail=50

The traceback will name the file and line. Common causes: missing migration, broken import, config typo.

### Port 80 already in use

Something on your machine is bound to port 80. In `.env`, change:

    NGINX_HTTP_PORT=8080

Then `make down && make up`, access via `http://localhost:8080`.

### `permission denied` on the docker socket

You're not in the docker group yet, or you didn't re-login after adding yourself. Close the terminal completely, reopen it, and try again.

### The frontend shows old content after a code change

Docker is serving a cached build. Fix:

    make fe-rebuild

That rebuilds the frontend image without cache, drops the shared volume, and restarts nginx.

---

## Where you fit — the ML interface

Every ML feature is called from a Celery task like this:

    # backend/app/tasks/detect.py
    from app.ml import _stub as ml     # <- change this line

    @shared_task(name="app.tasks.detect.remove_bg_task")
    def remove_bg_task(job_id: str) -> str:
        ...
        result = ml.remove_background(img, job.params)
        ...

The frozen interface is at **`backend/app/ml/base.py`**:

    @dataclass
    class MLResult:
        ok: bool
        output: Image.Image | dict | None = None
        meta: dict[str, Any] = field(default_factory=dict)
        error: str | None = None

    class Model:
        name: str = "unnamed"
        def load(self) -> None: ...
        def run(self, image: Image.Image, params: dict) -> MLResult: ...

### Rules

1. Every function takes `(image: PIL.Image, params: dict)` and returns `MLResult`. Never raise.
2. No file I/O. No DB. No Flask. No Celery. No HTTP.
3. Models load once at worker startup, not per call.
4. Document `params` and `meta` keys in `docs/ml-contracts.md`.

### The stub signatures you'll match

Look at `backend/app/ml/_stub.py`. All nine functions are there:

| Function | Input | Output |
|---|---|---|
| `remove_background` | image, `{replace_with}` | RGBA image |
| `inpaint` | image, `{prompt, steps}` | RGB image |
| `generate` | image (ignored), `{prompt, width, height}` | RGB image |
| `img2img` | image, `{prompt, strength}` | RGB image |
| `controlnet_scribble` | image, `{prompt, control_strength}` | RGB image |
| `detect_nsfw` | image, `{}` | `{nsfw_score, categories}` |
| `detect_ai` | image, `{}` | `{ai_probability, is_ai_generated}` |
| `detect_objects` | image, `{confidence_threshold}` | `{objects: [...]}` |
| `embed` | image, `{}` | `{vector: [512 floats], dim}` |

### Integration checklist

When you're ready to ship a real model:

1. Write `backend/app/ml/<your_module>.py`
2. Match the signature of the corresponding stub function
3. Test it in isolation — call the function from a Jupyter notebook or a standalone Python script with a sample `PIL.Image`
4. Push a branch: `git checkout -b feature/your-model`
5. Open a PR
6. I'll change one import line in the matching task file

That's the entire integration. Nothing else in the codebase changes.

---

## Where to ask for help

- **Broken stack:** check `make logs`
- **API question:** look at `docs/api-contract.md`
- **ML interface question:** look at `docs/ml-contracts.md`
- **Docker/infra:** ask Ayush

Enjoy the platform. It's a real one.
