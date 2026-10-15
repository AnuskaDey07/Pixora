"""Batch 4 Group A verification — structural checks."""
from __future__ import annotations

import inspect

from app import create_app
from app.tasks.celery_app import celery_app


def main() -> int:
    app = create_app()

    print("=" * 70)
    print("BATCH 4 — GROUP A VERIFICATION")
    print("=" * 70)

    with app.app_context():
        # 1. Task registration
        print("\n[1] Registered tasks")
        print("-" * 70)
        registered = sorted(t for t in celery_app.tasks if t.startswith("app.tasks"))
        for t in registered:
            print(f"  OK  {t}")

        expected_prefixes = [
            "app.tasks.basic",
            "app.tasks.detect",
            "app.tasks.generate",
            "app.tasks.search",
            "app.tasks.maintenance",
        ]
        for prefix in expected_prefixes:
            if not any(t.startswith(prefix) for t in registered):
                print(f"  MISSING tasks from {prefix}.*")

        # 2. Queue routing
        print("\n[2] Queue routing map")
        print("-" * 70)
        from app.services.jobs import JOB_TYPE_QUEUE, JOB_TYPE_TASK
        for jt in sorted(JOB_TYPE_QUEUE):
            q = JOB_TYPE_QUEUE[jt]
            task = JOB_TYPE_TASK.get(jt, "—none—")
            print(f"  {jt:18s} queue={q:6s} task={task}")

        # 3. Route consistency
        print("\n[3] Consistency check")
        print("-" * 70)
        routes = celery_app.conf.task_routes
        for jt, task_name in JOB_TYPE_TASK.items():
            routed = None
            for pattern, spec in routes.items():
                if task_name.startswith(pattern[:-1]):
                    routed = spec["queue"]
                    break
            declared = JOB_TYPE_QUEUE[jt]
            ok = "OK " if routed == declared else "BAD"
            print(f"  {ok} {jt:18s} declared={declared:6s} routed={routed}")

        # 4. ML stub functions
        print("\n[4] ML stub functions")
        print("-" * 70)
        from app.ml import _stub as ml
        for name in [
            "remove_background", "inpaint", "generate", "img2img",
            "controlnet_scribble", "detect_nsfw", "detect_ai",
            "detect_objects", "embed",
        ]:
            fn = getattr(ml, name, None)
            if fn is None:
                print(f"  MISSING {name}")
                continue
            sig = str(inspect.signature(fn))
            print(f"  OK  {name}{sig}")

        # 5. Every job type maps to a real task
        print("\n[5] Job type → task existence")
        print("-" * 70)
        for jt in sorted(JOB_TYPE_TASK):
            tn = JOB_TYPE_TASK[jt]
            found = tn in celery_app.tasks
            mark = "OK " if found else "BAD"
            print(f"  {mark} {jt:18s} → {tn}")

    print("\n" + "=" * 70)
    print("GROUP A: all checks should show OK")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
