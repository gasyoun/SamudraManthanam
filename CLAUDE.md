# CLAUDE.md

_Created: 12-05-2026 · Last updated: 16-08-2026_

`SamudraManthanam` («Пахтанье океана») is a **parallel Sanskrit–Russian corpus
search** platform: a FastAPI + SQLite FTS5 web app (the live public surface)
and a legacy Lazarus/Free Pascal Windows desktop client (`PO.EXE`). Same
corpus, two front ends.

Org conventions live in [`../CLAUDE.md`](https://github.com/gasyoun/github-spine/blob/main/CLAUDE.md).
Before encodings or corpus data, read the
[Sanskrit context primer](https://github.com/gasyoun/github-spine/blob/main/SANSKRIT_CONTEXT_PRIMER.md).

## How to run — web (primary)

```powershell
cd web
python -m uvicorn app.main:app --reload
$env:PYTHONPATH="."; python -m pytest -m "not corpus"
$env:PYTHONPATH="."; $env:USE_REAL_CORPUS="1"; python -m pytest -m "corpus"
```

Build the search DB: `./build-web-db.ps1`. Re-index (Docker): `./reindex.sh`.

Public search after a known production deploy (`root@193.232.229.92`,
`/opt/samudra`):
[https://samudra.193.232.229.92.sslip.io/](https://samudra.193.232.229.92.sslip.io/).
Recipe: `cd /opt/samudra/repo && git pull --ff-only origin main && /opt/samudra/venv/bin/pip install -r web/requirements.txt && systemctl restart samudra`.
Ops note on the box: `/opt/samudra/OPS.md`. Do **not** invent a second
deploy path. Corpus reindex is a separate explicit step, not the app restart.

Web layout: `web/app/dispatch_service.py` (all search modes),
`search_service.py` (FTS5 prefix + AND), `morph_service.py`,
`html_service.py` (Jinja2 fragments), `settings.py` (`DB_PATH`),
`models.py` (Pydantic v2). Tests:
`web/tests/test_api.py`, `test_golden_queries.py`, `test_contract.py`,
`test_morph.py`.

## How to run — desktop (legacy)

Open [`Index/Index_pr.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi)
in Lazarus (packages: TurboPowerIPro, LCL). Updater:
`Index/Updater/POUpdater.lpi`. Output: `Index/lib/x86_64-win64/`.
No CLI build script. Version constant `CURRENT_VERSION` in
[`Units/UpdateChecker.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/UpdateChecker.pas)
must be bumped on a desktop release (live `1.5.1`). Update JSON:
`https://samskrtam.ru/software-updates/po-ors.json`.

Runtime next to `PO.EXE`: `Data/` (corpus HTML), `Programdata/data.txt`
(filename list), `program.ini`, `program.grp`, `Search/` (result HTML).

## Do not touch

- Do not start a second desktop search engine or a second web indexer.
- Do not treat corpus reindex as part of the app `systemctl restart`.
- Do not rewrite `stenogrammy` / lesson-listen paths here — those belong
  to Systema / whisper keep-out rules, not this repo.
- Desktop `Index/lib/` build output is generated.

Danger facts:
[Uprava DANGER_FACTS.md](https://github.com/gasyoun/Uprava/blob/main/DANGER_FACTS.md)
and the generated block of
[AGENTS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/AGENTS.md).

## Agent skills

### Issue tracker

Native GitHub Issues, not Uprava handoffs. See [`docs/agents/issue-tracker.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/issue-tracker.md).

### Triage labels

Five-role vocabulary (`needs-triage` … `wontfix`) mapped onto this repo's actual label set. See [`docs/agents/triage-labels.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/triage-labels.md).

### Domain docs

No `CONTEXT.md`/`docs/adr/` here — the real reading-order chain and conflict rule live in `DOCUMENTATION_INDEX.md`. See [`docs/agents/domain.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/domain.md).

_Dr. Mārcis Gasūns_
