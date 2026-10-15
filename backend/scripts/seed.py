"""Populate Pixora with demo data.

Creates three users, uploads six generated images, fires a full set of
jobs against each image, waits for completion, and prints a summary.

Idempotent: existing users are skipped, but new images are always added.
Run with:

    docker compose exec api python scripts/seed.py
    # or
    make seed

Credentials after running:

    demo-admin@example.com  / demo-password-123  (admin)
    demo-alice@example.com  / demo-password-123  (user)
    demo-bob@example.com    / demo-password-123  (user)
"""
from __future__ import annotations

import io
import sys
import time
import uuid
from datetime import datetime, timezone

from PIL import Image, ImageDraw

from app import create_app
from app.extensions import db
from app.models.embedding import Embedding
from app.models.image import Image as ImageModel
from app.models.job import Job
from app.models.user import User
from app.services import imaging, jobs as jobs_service, storage
from app.services.security import hash_password


# ─────────────────────────────────────────────────────────────────────
# Sample images — generated with PIL, no files needed on disk
# ─────────────────────────────────────────────────────────────────────

def _gradient(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    """Vertical gradient between two RGB colors."""
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            img.putpixel((x, y), (r, g, b))
    return img


def _circle_pattern(w: int, h: int) -> Image.Image:
    """Concentric circles."""
    img = Image.new("RGB", (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    for r in range(min(w, h) // 2, 0, -20):
        color = (
            80 + (r * 3) % 175,
            100 + (r * 5) % 155,
            140 + (r * 7) % 115,
        )
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    return img


def _checkerboard(w: int, h: int, size: int = 40) -> Image.Image:
    """Checkerboard of two colors."""
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    for y in range(0, h, size):
        for x in range(0, w, size):
            if (x // size + y // size) % 2 == 0:
                draw.rectangle((x, y, x + size, y + size), fill=(30, 30, 50))
    return img


def _stripes(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(img)
    for i in range(0, w + h, 30):
        draw.line([(i, 0), (0, i)], fill=(230, 120, 60), width=8)
    return img


def _mountains(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (135, 206, 250))  # sky
    draw = ImageDraw.Draw(img)
    # sun
    draw.ellipse((w - 140, 40, w - 40, 140), fill=(255, 220, 80))
    # mountains
    draw.polygon([(0, h), (w // 3, h // 2), (w // 2, h * 3 // 4)], fill=(70, 90, 130))
    draw.polygon([(w // 3, h), (w * 2 // 3, h // 3), (w, h // 2), (w, h)], fill=(45, 65, 100))
    # ground
    draw.rectangle((0, h * 3 // 4, w, h), fill=(60, 130, 80))
    return img


def _flow_field(w: int, h: int) -> Image.Image:
    """Abstract color noise."""
    img = Image.new("RGB", (w, h))
    for y in range(h):
        for x in range(w):
            r = (x * 7 + y * 13) % 256
            g = (x * 11 + y * 5) % 256
            b = (x * 3 + y * 17) % 256
            img.putpixel((x, y), (r, g, b))
    return img


SAMPLE_IMAGES = [
    ("gradient-sunset.png",   lambda: _gradient(640, 480, (255, 100, 50),  (60, 30, 120))),
    ("gradient-ocean.png",    lambda: _gradient(800, 600, (135, 206, 235), (0, 40, 90))),
    ("circles.png",           lambda: _circle_pattern(600, 600)),
    ("checkerboard.png",      lambda: _checkerboard(640, 480)),
    ("stripes.png",           lambda: _stripes(700, 500)),
    ("mountains.png",         lambda: _mountains(800, 600)),
]


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# Seeding logic
# ─────────────────────────────────────────────────────────────────────

DEMO_USERS = [
    ("demo-admin@example.com", "demo-password-123", "admin"),
    ("demo-alice@example.com", "demo-password-123", "user"),
    ("demo-bob@example.com",   "demo-password-123", "user"),
]


def ensure_users() -> list[User]:
    users = []
    for email, password, role in DEMO_USERS:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            print(f"  created user: {email} ({role})")
        else:
            print(f"  user exists: {email} ({user.role})")
        users.append(user)
    return users


def upload_image(user: User, filename: str, img: Image.Image) -> ImageModel:
    data = _png_bytes(img)
    mime = "image/png"

    original_key = storage.make_key(f"originals/{user.id}", filename)
    thumb_key = storage.make_key(f"thumbs/{user.id}", f"{filename}.png")

    thumb_bytes = imaging.make_thumbnail(img)

    storage.upload_bytes("uploads", original_key, data, mime)
    storage.upload_bytes("thumbs", thumb_key, thumb_bytes, "image/png")

    record = ImageModel(
        user_id=user.id,
        original_key=original_key,
        thumb_key=thumb_key,
        filename=filename,
        mime=mime,
        size_bytes=len(data),
        width=img.width,
        height=img.height,
    )
    db.session.add(record)
    db.session.commit()
    return record


def create_job(user: User, image: ImageModel, job_type: str, params: dict) -> Job:
    job = jobs_service.create_job(
        user_id=user.id,
        job_type=job_type,
        image_id=image.id,
        params=params,
    )
    jobs_service.enqueue_job(job)
    return job


def wait_for_jobs(job_ids: list[str], timeout_s: int = 60) -> dict:
    """Block until all jobs are terminal. Returns {status: count}."""
    deadline = time.time() + timeout_s
    pending = set(job_ids)
    terminal_counts = {"done": 0, "failed": 0, "timeout": 0}

    while pending and time.time() < deadline:
        for jid in list(pending):
            j = Job.query.get(jid)
            if j is None:
                pending.discard(jid)
                continue
            if j.status in ("done", "failed", "timeout"):
                terminal_counts[j.status] += 1
                pending.discard(jid)
        if pending:
            time.sleep(1)
            db.session.expire_all()

    # Anything still pending counts as still-in-flight
    terminal_counts["pending"] = len(pending)
    return terminal_counts


def main() -> int:
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("PIXORA SEED — demo data")
        print("=" * 70)

        print("\n[1/4] Ensuring demo users...")
        users = ensure_users()

        print("\n[2/4] Uploading sample images...")
        images = []
        for i, (filename, maker) in enumerate(SAMPLE_IMAGES):
            user = users[i % len(users)]
            img = maker()
            record = upload_image(user, filename, img)
            images.append((record, user))
            print(f"  uploaded {filename:24s} → {user.email}  ({img.width}x{img.height})")

        print("\n[3/4] Firing jobs for each image...")
        all_jobs: list[str] = []
        for record, user in images:
            for job_type, params in [
                ("resize",         {"width": 256, "height": 256}),
                ("convert",        {"format": "JPEG"}),
                ("detect_nsfw",    {}),
                ("embed",          {}),
                ("remove_bg",      {}),
            ]:
                try:
                    job = create_job(user, record, job_type, params)
                    all_jobs.append(str(job.id))
                except Exception as exc:
                    print(f"  [warn] {job_type} for {record.filename}: {exc}")

        print(f"  queued {len(all_jobs)} jobs across {len(images)} images")

        print("\n[4/4] Waiting for jobs to complete...")
        counts = wait_for_jobs(all_jobs, timeout_s=90)
        print(f"  done:    {counts.get('done', 0)}")
        print(f"  failed:  {counts.get('failed', 0)}")
        print(f"  timeout: {counts.get('timeout', 0)}")
        print(f"  pending: {counts.get('pending', 0)}  (GPU jobs need worker-gpu running)")

        # Summary
        total_users = User.query.count()
        total_images = ImageModel.query.count()
        total_jobs = Job.query.count()
        total_embeddings = Embedding.query.count()

        print("\n" + "=" * 70)
        print("SEED COMPLETE")
        print("=" * 70)
        print(f"  users:      {total_users}")
        print(f"  images:     {total_images}")
        print(f"  jobs:       {total_jobs}")
        print(f"  embeddings: {total_embeddings}")
        print()
        print("Demo credentials:")
        print("  demo-admin@example.com  /  demo-password-123  (admin)")
        print("  demo-alice@example.com  /  demo-password-123")
        print("  demo-bob@example.com    /  demo-password-123")
        print()
        print("Open http://localhost and log in as the admin to see everything.")
        print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
