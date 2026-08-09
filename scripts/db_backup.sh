#!/usr/bin/env bash
# Daily backup of corpus.db + state.db with 7-day retention.
# Installed at /usr/local/sbin/samudra-db-backup.sh on prod (H2389).
# Cron: /etc/cron.d/samudra-db-backup — 03:07 UTC daily.
set -euo pipefail

BACKUP_DIR=/opt/samudra/db/backups
DB_DIR=/opt/samudra/db
STAMP=$(date +%Y%m%d_%H%M%S)
RETAIN_DAYS=7
LOG_TAG="samudra-db-backup"

mkdir -p "$BACKUP_DIR"

for db in corpus state; do
    src="$DB_DIR/${db}.db"
    dst="$BACKUP_DIR/${db}_${STAMP}.db"
    if [ -f "$src" ]; then
        sqlite3 "$src" ".backup $dst"
        echo "$(date -Iseconds) [$LOG_TAG] OK: $src -> $dst"
    else
        echo "$(date -Iseconds) [$LOG_TAG] SKIP: $src not found" >&2
    fi
done

# Purge backups older than RETAIN_DAYS days (including stale -shm/-wal sidecars)
find "$BACKUP_DIR" -maxdepth 1 \
    \( -name '*.db' -o -name '*.db-shm' -o -name '*.db-wal' \) \
    -mtime +"$RETAIN_DAYS" -delete
echo "$(date -Iseconds) [$LOG_TAG] retention sweep done (>${RETAIN_DAYS}d purged)"
