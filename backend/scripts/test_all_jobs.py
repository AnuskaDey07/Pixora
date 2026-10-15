"""Fire one job of each type via HTTP and poll for completion."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

API = os.environ.get("API_BASE", "http://api:5000")
EMAIL = os.environ.get("TEST_EMAIL", "ayush@example.com")
PASSWORD = os.environ.get("TEST_PASSWORD", "password123")


def _req(method, path, data=None, token=None):
    url = f"{API}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read())


def main() -> int:
    print("Logging in...")
    login = _req("POST", "/api/auth/login", {"email": EMAIL, "password": PASSWORD})
    token = login["access_token"]
    print(f"  token: {len(token)} chars")

    images = _req("GET", "/api/images?limit=1", token=token)
    if not images["images"]:
        print("  no images; upload one first")
        return 1
    img_id = images["images"][0]["id"]
    print(f"  image: {img_id}")

    jobs = [
        ("resize",          {"type": "resize", "image_id": img_id, "params": {"width": 128, "height": 128}}),
        ("convert",         {"type": "convert", "image_id": img_id, "params": {"format": "JPEG"}}),
        ("detect_nsfw",     {"type": "detect_nsfw", "image_id": img_id, "params": {}}),
        ("detect_ai",       {"type": "detect_ai", "image_id": img_id, "params": {}}),
        ("detect_objects",  {"type": "detect_objects", "image_id": img_id, "params": {}}),
        ("remove_bg",       {"type": "remove_bg", "image_id": img_id, "params": {}}),
        ("embed",           {"type": "embed", "image_id": img_id, "params": {}}),
        ("generate",        {"type": "generate", "params": {"prompt": "test"}}),
        ("img2img",         {"type": "img2img", "image_id": img_id, "params": {"prompt": "test"}}),
        ("inpaint",         {"type": "inpaint", "image_id": img_id, "params": {"prompt": "test"}}),
        ("controlnet",      {"type": "controlnet", "image_id": img_id, "params": {"prompt": "test"}}),
    ]

    print("\nFiring jobs...")
    print(f"{'type':<18} {'job id':<38} status")
    print("-" * 70)

    results = []
    for label, body in jobs:
        try:
            job = _req("POST", "/api/jobs", body, token=token)
            jid = job["id"]
            status = job["status"]
            time.sleep(4)
            polled = _req("GET", f"/api/jobs/{jid}", token=token)
            status = polled["status"]
            print(f"{label:<18} {jid:<38} {status}")
            results.append((label, status))
        except Exception as exc:
            print(f"{label:<18} {'—':<38} ERROR: {exc}")
            results.append((label, "error"))

    print("\nSummary")
    print("-" * 70)
    done = sum(1 for _, s in results if s == "done")
    pending = sum(1 for _, s in results if s in ("pending", "running"))
    failed = sum(1 for _, s in results if s in ("failed", "timeout", "error"))
    print(f"  done:    {done}")
    print(f"  pending: {pending}  (likely GPU jobs — start worker-gpu)")
    print(f"  failed:  {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
