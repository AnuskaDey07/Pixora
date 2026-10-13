"""Promote an existing user to admin, or create one.

Usage:
    docker compose exec api python scripts/create_admin.py <email>
    docker compose exec api python scripts/create_admin.py <email> --create
"""
from __future__ import annotations

import argparse
import sys

from app import create_app
from app.extensions import db
from app.models.user import User
from app.services.security import hash_password


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email address of the admin user")
    parser.add_argument("--create", action="store_true", help="create the user if not found")
    parser.add_argument("--password", default=None, help="password if creating")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=args.email.lower()).first()

        if user is None:
            if not args.create:
                print(f"user {args.email} not found (add --create to make them)", file=sys.stderr)
                return 1
            if not args.password:
                print("--password required when using --create", file=sys.stderr)
                return 1
            user = User(
                email=args.email.lower(),
                password_hash=hash_password(args.password),
                role="admin",
            )
            db.session.add(user)
            db.session.commit()
            print(f"created admin {user.email}")
            return 0

        user.role = "admin"
        user.is_active = True
        user.disabled_at = None
        db.session.commit()
        print(f"promoted {user.email} to admin")
        return 0


if __name__ == "__main__":
    sys.exit(main())
