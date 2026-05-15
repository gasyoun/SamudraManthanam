#!/bin/bash

# Configuration
CONTAINER_NAME="samudra_manthanam_web"
CORPUS_PATH="/corpus"
DB_PATH="/app/corpus.db"

echo "[$(date)] Starting daily re-indexing..."

# Run ingestion inside the running container
docker exec $CONTAINER_NAME python ingest/ingest.py --corpus-path $CORPUS_PATH --db-path $DB_PATH

if [ $? -eq 0 ]; then
    echo "[$(date)] Re-indexing complete."
else
    echo "[$(date)] Error: Re-indexing failed."
    exit 1
fi
