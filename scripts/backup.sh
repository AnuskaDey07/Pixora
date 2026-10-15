#!/usr/bin/env bash
# Pixora — full backup.
#
# Dumps Postgres and tars the MinIO data volume into a single
# timestamped archive.
#
# Usage:
#     ./scripts/backup.sh
#     ./scripts/backup.sh /path/to/backups-dir
#
# Output:
#     <dir>/pixora-backup-YYYYMMDD-HHMMSS.tar.gz
#
# Contents:
#     postgres.sql              pg_dump --clean --if-exists
#     minio/minio-data.tar.gz   tar of the pixora_minio_data volume
#     manifest.txt              metadata (date, sizes)

set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR="${1:-./backups}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
WORK_DIR="$(mktemp -d)"
ARCHIVE_NAME="pixora-backup-${STAMP}.tar.gz"

cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

mkdir -p "$BACKUP_DIR"

echo "=== Pixora backup — $STAMP ==="
echo "Output: $BACKUP_DIR/$ARCHIVE_NAME"
echo

# ── Postgres dump ────────────────────────────────────────────
echo "[1/3] Dumping Postgres..."
docker compose exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-pixora}" "${POSTGRES_DB:-pixora}" \
    --clean --if-exists --no-owner --no-acl \
    > "$WORK_DIR/postgres.sql"
PG_SIZE=$(du -h "$WORK_DIR/postgres.sql" | cut -f1)
echo "      postgres.sql — $PG_SIZE"

# ── MinIO volume backup ──────────────────────────────────────
echo "[2/3] Backing up MinIO volume..."
mkdir -p "$WORK_DIR/minio"
docker run --rm \
    -v pixora_minio_data:/data:ro \
    -v "$WORK_DIR/minio:/backup" \
    alpine:3.20 \
    tar -czf /backup/minio-data.tar.gz -C /data . \
    2>/dev/null || {
        echo "      [warn] MinIO volume backup failed — continuing without it"
        touch "$WORK_DIR/minio/EMPTY"
    }
MINIO_SIZE=$(du -sh "$WORK_DIR/minio" 2>/dev/null | cut -f1 || echo "0")
echo "      minio/ — $MINIO_SIZE"

# ── Manifest ─────────────────────────────────────────────────
echo "[3/3] Writing manifest..."
{
    echo "Pixora backup"
    echo "Date (UTC):        $STAMP"
    echo "Postgres size:     $PG_SIZE"
    echo "MinIO size:        $MINIO_SIZE"
    echo "Postgres version:  $(docker compose exec -T postgres postgres --version 2>/dev/null | head -1 || echo 'unknown')"
    echo "Buckets (via volume): pixora-uploads pixora-thumbs pixora-results pixora-masks"
} > "$WORK_DIR/manifest.txt"

# ── Tarball ──────────────────────────────────────────────────
echo
echo "Creating archive..."
tar -czf "$BACKUP_DIR/$ARCHIVE_NAME" -C "$WORK_DIR" .
FINAL_SIZE=$(du -h "$BACKUP_DIR/$ARCHIVE_NAME" | cut -f1)

echo
echo "=== Backup complete ==="
echo "File: $BACKUP_DIR/$ARCHIVE_NAME ($FINAL_SIZE)"
echo

# ── Retention: keep last 7 ───────────────────────────────────
KEEP=7
COUNT=$(find "$BACKUP_DIR" -name "pixora-backup-*.tar.gz" | wc -l)
if [ "$COUNT" -gt "$KEEP" ]; then
    echo "Pruning old backups (keeping last $KEEP)..."
    find "$BACKUP_DIR" -name "pixora-backup-*.tar.gz" -printf '%T@ %p\n' \
        | sort -n | head -n "-$KEEP" | cut -d' ' -f2- | xargs -r rm -f
    echo "Pruned."
fi
