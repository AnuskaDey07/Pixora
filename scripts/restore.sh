#!/usr/bin/env bash
# Pixora — restore from a backup tarball.
#
# DANGER: this overwrites the current database and MinIO volume.
# It prompts for confirmation before doing anything destructive.
#
# Usage:
#     ./scripts/restore.sh backups/pixora-backup-20261015-120000.tar.gz

set -euo pipefail

cd "$(dirname "$0")/.."

if [ $# -ne 1 ]; then
    echo "Usage: $0 <path-to-backup.tar.gz>"
    exit 1
fi

ARCHIVE="$1"
if [ ! -f "$ARCHIVE" ]; then
    echo "Backup file not found: $ARCHIVE"
    exit 1
fi

echo "=== Pixora restore ==="
echo "Archive: $ARCHIVE"
echo
echo "This will:"
echo "  - OVERWRITE the current Postgres database"
echo "  - OVERWRITE the MinIO data volume"
echo
read -p "Type 'restore' to continue: " CONFIRM
if [ "$CONFIRM" != "restore" ]; then
    echo "Aborted."
    exit 1
fi

WORK_DIR="$(mktemp -d)"
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

echo
echo "[1/4] Extracting archive..."
tar -xzf "$ARCHIVE" -C "$WORK_DIR"
cat "$WORK_DIR/manifest.txt" 2>/dev/null || true
echo

echo "[2/4] Restoring Postgres..."
docker compose exec -T postgres \
    psql -U "${POSTGRES_USER:-pixora}" -d "${POSTGRES_DB:-pixora}" \
    < "$WORK_DIR/postgres.sql"
echo "      Postgres restored."
echo

echo "[3/4] Restoring MinIO volume..."
if [ -f "$WORK_DIR/minio/minio-data.tar.gz" ]; then
    docker run --rm \
        -v pixora_minio_data:/data \
        -v "$WORK_DIR/minio:/backup:ro" \
        alpine:3.20 \
        sh -c "rm -rf /data/* && tar -xzf /backup/minio-data.tar.gz -C /data"
    echo "      MinIO volume restored."
else
    echo "      No MinIO data in archive — skipped."
fi
echo

echo "[4/4] Restarting API and workers..."
docker compose restart api worker-light worker-ml worker-beat >/dev/null
echo "      Restarted."
echo

echo "=== Restore complete ==="
echo "Verify: curl http://localhost/api/health"
