"""Block until Postgres accepts connections, then exit 0."""
from __future__ import annotations

import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set", file=sys.stderr)
        return 1

    engine = create_engine(url, pool_pre_ping=True, future=True)
    deadline = time.time() + 60
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Postgres ready (attempt {attempt})")
            return 0
        except OperationalError as exc:
            print(f"waiting for postgres (attempt {attempt}): {exc.orig}")
            time.sleep(2)
        except Exception as exc:
            print(f"unexpected error: {exc}")
            time.sleep(2)

    print("Postgres not ready after 60s", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
