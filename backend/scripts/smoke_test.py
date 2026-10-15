"""Pixora — full end-to-end smoke test.

Runs against a live stack via HTTP (default: http://api:5000).
Exercises: health, auth, images, jobs (all 11 types), search, admin,
and verifies results actually landed in MinIO.

Usage (inside the api container):
    python scripts/smoke_test.py
    API_BASE=http://api:5000 TEST_EMAIL=... TEST_PASSWORD=... python scripts/smoke_test.py

Exit code: 0 = all pass, 1 = at least one failure.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API = os.environ.get("API_BASE", "http://api:5000")
EMAIL = os.environ.get("TEST_EMAIL", "ayush@example.com")
PASSWORD = os.environ.get("TEST_PASSWORD", "password123")
JOB_TIMEOUT_S = int(os.environ.get("JOB_TIMEOUT_S", "30"))

# Track results
PASS: list[str] = []
FAIL: list[tuple[str, str]] = []


def ok(label: str) -> None:
    PASS.append(label)
    print(f"  \033[92mPASS\033[0m  {label}")


def bad(label: str, detail: str) -> None:
    FAIL.append((label, detail))
    print(f"  \033[91mFAIL\033[0m  {label} — {detail}")


def section(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")
    print("-" * 70)


def request(method: str, path: str, *, data=None, token=None, multipart=None, timeout=30):
    url = f"{API}{path}"
    headers = {}
    body = None

    if multipart is not None:
        boundary = f"----pixora{uuid.uuid4().hex}"
        parts = []
        for field, value in multipart.get("fields", {}).items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{field}"\r\n\r\n'.encode())
            parts.append(f"{value}\r\n".encode())
        for field, (filename, content, ctype) in multipart.get("files", {}).items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
            )
            parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
            parts.append(content)
            parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw.decode()) if raw else None
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode()) if raw else None
        except json.JSONDecodeError:
            return e.code, raw.decode(errors="replace")


def make_test_png(w: int = 512, h: int = 512) -> bytes:
    """Create a test PNG without relying on PIL on the host."""
    # Minimal valid PNG via PIL inside the container
    from PIL import Image
    img = Image.new("RGB", (w, h), (200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# 1. Health
# ─────────────────────────────────────────────────────────────────────
section("[1] Health")
s, data = request("GET", "/api/health")
if s == 200 and data and data.get("status") == "ok":
    ok("GET /api/health")
else:
    bad("GET /api/health", f"status={s} body={data}")
    print("\nAPI is not reachable — aborting.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────
# 2. Auth
# ─────────────────────────────────────────────────────────────────────
section("[2] Auth")

# Register (may 409 if user exists — treat both as pass)
test_email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
s, data = request("POST", "/api/auth/register", data={"email": test_email, "password": "password123"})
if s == 201:
    ok(f"register new user ({test_email})")
elif s == 409:
    ok("register: email already taken (expected)")
else:
    bad("register", f"status={s} body={data}")

# Login as the known admin
s, data = request("POST", "/api/auth/login", data={"email": EMAIL, "password": PASSWORD})
if s == 200 and data and "access_token" in data:
    ok(f"login as {EMAIL}")
    token = data["access_token"]
    refresh = data.get("refresh_token")
else:
    bad("login", f"status={s} body={data}")
    print("\nCannot proceed without an auth token.")
    sys.exit(1)

# /me
s, data = request("GET", "/api/auth/me", token=token)
if s == 200 and data.get("email") == EMAIL:
    ok("GET /api/auth/me")
    is_admin = data.get("role") == "admin"
else:
    bad("GET /api/auth/me", f"status={s} body={data}")
    is_admin = False

# Refresh
if refresh:
    s, data = request("POST", "/api/auth/refresh", data={"refresh_token": refresh})
    if s == 200 and data and "access_token" in data:
        ok("POST /api/auth/refresh")
    else:
        bad("refresh", f"status={s} body={data}")

# Unauthorized
s, _ = request("GET", "/api/auth/me")
if s == 401:
    ok("GET /api/auth/me without token returns 401")
else:
    bad("unauthorized check", f"expected 401, got {s}")

# Bad login
s, _ = request("POST", "/api/auth/login", data={"email": EMAIL, "password": "wrong"})
if s == 401:
    ok("login with wrong password returns 401")
else:
    bad("bad login check", f"expected 401, got {s}")


# ─────────────────────────────────────────────────────────────────────
# 3. Images
# ─────────────────────────────────────────────────────────────────────
section("[3] Images")

png_bytes = make_test_png(640, 480)

s, data = request(
    "POST", "/api/images/upload",
    token=token,
    multipart={"files": {"file": ("smoke.png", png_bytes, "image/png")}},
)
if s == 201 and data and "id" in data:
    ok(f"upload image ({data['width']}x{data['height']})")
    image_id = data["id"]
    if data.get("thumb_url", "").startswith("http://localhost:9000"):
        ok("thumb_url uses public endpoint")
    else:
        bad("thumb_url endpoint", f"got {data.get('thumb_url')}")
else:
    bad("upload", f"status={s} body={data}")
    sys.exit(1)

# Upload rejects junk
s, _ = request(
    "POST", "/api/images/upload",
    token=token,
    multipart={"files": {"file": ("bad.png", b"not an image", "image/png")}},
)
if s == 415:
    ok("upload rejects non-image bytes (415)")
else:
    bad("upload junk check", f"expected 415, got {s}")

# List
s, data = request("GET", "/api/images?limit=5", token=token)
if s == 200 and data and data.get("count", 0) >= 1:
    ok(f"list images (count={data['count']})")
else:
    bad("list images", f"status={s} body={data}")

# Get
s, data = request("GET", f"/api/images/{image_id}", token=token)
if s == 200 and data.get("id") == image_id:
    ok(f"get image {image_id[:8]}…")
else:
    bad("get image", f"status={s} body={data}")

# 404 for unknown
s, _ = request("GET", f"/api/images/{uuid.uuid4()}", token=token)
if s == 404:
    ok("get unknown image returns 404")
else:
    bad("unknown image check", f"expected 404, got {s}")


# ─────────────────────────────────────────────────────────────────────
# 4. Jobs — fire one of each type
# ─────────────────────────────────────────────────────────────────────
section("[4] Jobs — one per type")

JOB_CASES = [
    ("resize",         {"image_id": image_id, "params": {"width": 128, "height": 128}}, True),
    ("convert",        {"image_id": image_id, "params": {"format": "JPEG"}}, True),
    ("detect_nsfw",    {"image_id": image_id, "params": {}}, True),
    ("detect_ai",      {"image_id": image_id, "params": {}}, True),
    ("detect_objects", {"image_id": image_id, "params": {}}, True),
    ("remove_bg",      {"image_id": image_id, "params": {}}, True),
    ("embed",          {"image_id": image_id, "params": {}}, True),
    ("generate",       {"params": {"prompt": "smoke test", "width": 256, "height": 256}}, True),
    ("img2img",        {"image_id": image_id, "params": {"prompt": "smoke"}}, True),
    ("inpaint",        {"image_id": image_id, "params": {"prompt": "smoke"}}, True),
    ("controlnet",     {"image_id": image_id, "params": {"prompt": "smoke"}}, True),
]

job_ids: dict[str, str] = {}

for jt, payload, expect_done in JOB_CASES:
    body = {"type": jt, **payload}
    s, data = request("POST", "/api/jobs", data=body, token=token)
    if s == 202 and data and "id" in data:
        job_ids[jt] = data["id"]
        print(f"  queued  {jt:16s} job {data['id'][:8]}…")
    else:
        bad(f"create job {jt}", f"status={s} body={data}")

# Unknown job type
s, _ = request("POST", "/api/jobs", data={"type": "does_not_exist"}, token=token)
if s == 400:
    ok("unknown job type returns 400")
else:
    bad("unknown job type check", f"expected 400, got {s}")

# Poll all jobs until done / timeout
print()
deadline = time.time() + JOB_TIMEOUT_S
pending = dict(job_ids)
results: dict[str, dict] = {}

while pending and time.time() < deadline:
    for jt in list(pending):
        s, data = request("GET", f"/api/jobs/{pending[jt]}", token=token)
        if s != 200:
            bad(f"poll {jt}", f"status={s}")
            pending.pop(jt)
            continue
        if data["status"] in ("done", "failed", "timeout"):
            results[jt] = data
            pending.pop(jt)
    if pending:
        time.sleep(1)

for jt, expected in [(c[0], c[2]) for c in JOB_CASES]:
    if jt not in results:
        bad(f"job {jt}", f"did not finish within {JOB_TIMEOUT_S}s (still pending)")
        continue
    r = results[jt]
    if r["status"] == "done":
        ok(f"job {jt:16s} done ({r.get('meta') or 'no meta'})")
    elif r["status"] in ("failed", "timeout"):
        bad(f"job {jt}", f"status={r['status']} error={r.get('error')}")
    else:
        bad(f"job {jt}", f"unexpected status {r['status']}")


# ─────────────────────────────────────────────────────────────────────
# 5. Search
# ─────────────────────────────────────────────────────────────────────
section("[5] Search")

s, data = request("POST", "/api/search/semantic", data={"query": "cat", "limit": 5}, token=token)
if s == 200 and data is not None:
    ok(f"semantic search ({data.get('count', 0)} results)")
else:
    bad("semantic search", f"status={s} body={data}")

s, data = request("POST", "/api/search/similar", data={"image_id": image_id, "limit": 5}, token=token)
if s == 200 and data is not None:
    ok(f"similar search ({data.get('count', 0)} results)")
else:
    bad("similar search", f"status={s} body={data}")

s, _ = request("POST", "/api/search/semantic", data={"query": ""}, token=token)
if s == 400:
    ok("semantic search with empty query returns 400")
else:
    bad("empty query check", f"expected 400, got {s}")


# ─────────────────────────────────────────────────────────────────────
# 6. Admin
# ─────────────────────────────────────────────────────────────────────
section("[6] Admin")

if not is_admin:
    print("  user is not admin — skipping admin tests")
else:
    s, data = request("GET", "/api/admin/users", token=token)
    if s == 200 and "users" in data:
        ok(f"list users ({data['count']})")
    else:
        bad("list users", f"status={s}")

    s, data = request("GET", "/api/admin/jobs?limit=5", token=token)
    if s == 200 and "jobs" in data:
        ok(f"list all jobs ({data['count']})")
    else:
        bad("list all jobs", f"status={s}")

    s, data = request("GET", "/api/admin/nsfw-queue", token=token)
    if s == 200 and "images" in data:
        ok(f"nsfw queue ({data['count']} flagged)")
    else:
        bad("nsfw queue", f"status={s}")


# ─────────────────────────────────────────────────────────────────────
# 7. Storage — verify results actually landed in MinIO
# ─────────────────────────────────────────────────────────────────────
section("[7] Storage")

# Find a done job with a result_url from section 4
done_results = [
    (jt, r) for jt, r in results.items()
    if r.get("status") == "done" and r.get("result_url")
]

if not done_results:
    bad("storage check", "no job produced a result_url to verify")
else:
    jt, r = done_results[0]
    # The presigned URL is signed for localhost:9000 (browser-facing).
    # Inside the container we hit MinIO directly with the internal client
    # and credentials — that tests "did the object actually land?"
    from app.config import get_settings
    from app.services import storage as storage_svc

    # The result_key is in the DB, not in the API response. Fetch it.
    s2, job_body = request("GET", f"/api/jobs/{r['id']}", token=token)
    # API doesn't return result_key — hit the DB directly for this check.
    from app import create_app
    from app.models.job import Job
    app = create_app()
    with app.app_context():
        job_row = Job.query.get(r["id"])
        if job_row is None or not job_row.result_key:
            bad("storage check", "job has no result_key in DB")
        else:
            try:
                raw = storage_svc.download_bytes("results", job_row.result_key)
                if len(raw) > 0:
                    ok(f"fetched {jt} result from MinIO ({len(raw)} bytes)")
                else:
                    bad("storage fetch", "empty body")
            except Exception as exc:
                bad("storage fetch", str(exc))

    # Also: presigned URL shape check (host header + signature present)
    url = r["result_url"]
    if url.startswith("http://localhost:9000/") and "X-Amz-Signature=" in url:
        ok("presigned URL is signed for public endpoint")
    else:
        bad("presigned URL shape", f"got {url[:80]}…")


# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
section("Summary")
print(f"  \033[92mPASS\033[0m: {len(PASS)}")
print(f"  \033[91mFAIL\033[0m: {len(FAIL)}")

if FAIL:
    print("\nFailures:")
    for label, detail in FAIL:
        print(f"  - {label}: {detail}")

print()
sys.exit(0 if not FAIL else 1)
