# Gemini Flash Phase 01: Foundation

Goal: prepare storage, settings, and no-Docker runtime foundations before feature work.

## Task 1.1: Centralize Settings

Files:

- `web/app/settings.py`
- tests if needed

Implement:

- Add `APP_ENV`.
- Add `DB_PATH`.
- Add `STATE_DB_PATH`.
- Add `CORPUS_PATH`.
- Add `PUBLIC_BASE_URL`.
- Add `ALLOWED_ORIGINS`.
- Keep default local development values.

Acceptance:

- Existing tests pass.
- Test fixtures can still override DB path.

## Task 1.2: Add `state.db`

Files:

- new `web/app/state_db.py`
- `web/app/db.py` if shared helpers are useful
- tests

Implement:

- Async connection helper for `STATE_DB_PATH`.
- Schema creation function for mutable platform data.
- Initial tables may be empty except a migration/version table.
- Do not move production data yet.

Acceptance:

- App can create/open `state.db`.
- Unit test verifies schema init is idempotent.

## Task 1.3: Add Health Endpoint

Files:

- new `web/app/routers/health.py`
- `web/app/main.py`
- tests

Implement:

- `GET /api/health`.
- Check app status.
- Check `corpus.db` is readable.
- Check `state.db` is readable.
- Return source count if corpus DB exists.

Acceptance:

- Health passes with test DB.
- Missing DB returns controlled degraded status, not traceback.

## Task 1.4: Prepare No-Docker VPS Docs

Files:

- `README.md` or new `DEPLOY_VPS.md`
- possibly `deploy/` scripts

Implement:

- Python venv setup.
- systemd service example.
- nginx reverse proxy note.
- environment variables.
- DB upload location.

Acceptance:

- A VPS install path is clear without Docker.

## Checks

```powershell
py -3.10 -m compileall web\app web\ingest
cd web
python -m pytest
```
