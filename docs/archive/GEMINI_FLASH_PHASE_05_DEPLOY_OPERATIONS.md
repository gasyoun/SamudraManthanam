_Created: 25-08-2026 · Last updated: 05-09-2026_

# Gemini Flash Phase 05: Deploy and Operations

Goal: make corpus publication and VPS operation repeatable without Docker.

## Task 5.1: Corpus Metadata

Files:

- `web/app/db.py`
- `web/ingest/ingest.py`
- tests

Implement `corpus_meta` keys:

- corpus_version,
- build_time,
- source_count,
- line_count,
- manifest_sha256.

Acceptance:

- Export/search can read corpus version.

## Task 5.2: Corpus Validation Script

Files:

- new `web/tools/validate_corpus.py`
- docs/tests if practical

Validate:

- DB exists,
- `PRAGMA integrity_check`,
- source count plausible,
- line count plausible,
- no duplicate filenames,
- no empty source titles,
- smoke queries pass.

Acceptance:

- Script exits nonzero on validation failure.

## Task 5.3: Atomic Publish Script

Files:

- new `deploy/publish_corpus.sh`
- docs

Implement:

- accept active DB path,
- accept next DB path,
- validate next DB,
- backup current DB,
- atomic swap,
- post-publish smoke check.

Acceptance:

- Failed validation does not replace current DB.

## Task 5.4: VPS Service Files

Files:

- `DEPLOY_VPS.md`
- optional `deploy/samudra.service.example`
- optional `deploy/nginx.samudra.example`

Document:

- venv setup,
- env file,
- systemd service,
- nginx reverse proxy,
- DB upload location,
- restart commands.

## Task 5.5: Rollback Procedure

Document backup location, restore command, smoke checks, and restart command.

Acceptance:

- Rollback can be performed without Git changes.

## Operational Rule

`corpus.db` and `state.db` must never be committed.

## Checks

```powershell
git diff --check
bash -n deploy/*.sh
```

_Dr. Mārcis Gasūns_
