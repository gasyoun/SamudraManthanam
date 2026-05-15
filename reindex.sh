#!/bin/bash
# Corpus publish script — no Docker required.
# Validates, ingests into a temp DB, integrity-checks, backs up, and atomically swaps.
#
# Environment variables (all have defaults):
#   CORPUS_PATH    Path to the corpus directory (Data/ + Programdata/)
#   DB_PATH        Path to the live corpus.db
#   NEXT_DB_PATH   Temp DB built before the swap (cleaned up on success)
#   BACKUP_DIR     Directory for timestamped backups
#   VENV           Path to the Python venv (if using one)
#   MIN_SOURCES    Minimum source count accepted by smoke-check (default: 1)

set -euo pipefail

CORPUS_PATH="${CORPUS_PATH:-/corpus}"
DB_PATH="${DB_PATH:-/app/corpus.db}"
NEXT_DB_PATH="${NEXT_DB_PATH:-/app/corpus.next.db}"
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
VENV="${VENV:-}"
MIN_SOURCES="${MIN_SOURCES:-1}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting corpus publish…"
echo "  corpus:   $CORPUS_PATH"
echo "  live db:  $DB_PATH"
echo "  temp db:  $NEXT_DB_PATH"
echo "  backups:  $BACKUP_DIR"

# Activate virtualenv if provided
if [ -n "$VENV" ]; then
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web"

cd "$WEB_DIR"

PYTHONPATH="$WEB_DIR" python ingest/publish.py \
    --corpus-path  "$CORPUS_PATH"  \
    --db-path      "$DB_PATH"      \
    --next-db-path "$NEXT_DB_PATH" \
    --backup-dir   "$BACKUP_DIR"   \
    --min-sources  "$MIN_SOURCES"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Publish complete."
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Publish FAILED (exit $EXIT_CODE)." >&2
    exit $EXIT_CODE
fi
