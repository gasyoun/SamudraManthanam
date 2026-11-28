# CLAUDE.md

_Created: 12-05-2026 · Last updated: 28-11-2026 — H8658 truth refresh: public URL is the branded host, H7790 dictionary layer, changelog-queue and agent-policy fences, desktop runtime paths; H7934 Python floor sync rule added_

This repo is **SamudraManthanam** («Пахтанье океана») — a **parallel
Sanskrit–Russian corpus search** platform: a FastAPI + SQLite FTS5 web app
(the live public surface) and a legacy Lazarus/Free Pascal Windows desktop
client (`PO.EXE`). Same corpus, two front ends.

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

Build the search DB: `./build-web-db.ps1`. Corpus publish / re-index: `./reindex.sh` — validate, ingest into a temp DB, integrity-check, back up, atomic swap; Docker-path defaults, on prod through `CORPUS_PATH`/`DB_PATH`/… (`OPS.md`).

Public search after a known production deploy (`root@193.232.229.92`,
`/opt/samudra`): [https://samudra.samskrte.ru/](https://samudra.samskrte.ru/)
— the branded host (H2391). The older `samudra.193.232.229.92.sslip.io` name
fails TLS: the certificate served since 14-10-2026 covers the branded host
only.
Recipe: `cd /opt/samudra/repo && git pull --ff-only origin main && /opt/samudra/venv/bin/pip install -r web/requirements.txt && systemctl restart samudra`.
Ops note: [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md)
(tracked; on the box under `/opt/samudra/repo/`). Do **not** invent a second
deploy path. Corpus reindex is a separate explicit step, not the app restart.
A second unit, `deploy/samudra-word-of-day.service` (H4955; oneshot, fired
00:05 by `samudra-word-of-day.timer`) regenerates the daily word-of-the-day
record and posts it — also separate from the app restart.

Web layout: HTTP layer in `web/app/routers/` (one file per route family:
`search.py`, `search_page.py`, `morph.py`, `ai.py`, `word_of_day.py`,
`dict.py`, …), service logic in `web/app/services/` — `dispatch_service.py`
(all search modes), `search_service.py` (FTS5 prefix + AND),
`morph_service.py`, `html_service.py` (Jinja2 fragments), `dict_service.py` —
plus `web/app/settings.py` (`DB_PATH`), `web/app/models.py` (Pydantic v2).
Tests: `web/tests/test_api.py`, `test_golden_queries.py`, `test_contract.py`,
`test_morph.py`, `test_dict_ui.py`.

Word-of-the-day (H4955): the committed Kochergina pool
`web/app/data/word_of_day_pool.jsonl` feeds `scripts/word_of_day_generate.py`
(nightly; also Telegram-post hook `word_of_day_post.py`), which writes a
precomputed static record the router only reads — no per-request DB query.

Dictionaries (H7790, #463, 18-11-2026): `/slovari` is a first-class surface
over the five RU Sanskrit dictionaries (Frish, Kochergina, Kossovich, Knauer,
Smirnova — JSONL under `web/corpus_builder/jsonl/`): landing page, per-dict
varṇamālā index, structured entry pages, headword lookup in
Devanagari/IAST/SLP1, reverse RU→Sa gloss search, all read from the corpus
DB. The same commit moved the corpus manifest pin to bundle 2026.11
(mojibake-repaired dict JSONL): a code deploy brings the pages, a corpus
reindex brings the repaired text. Mojibake repair
(`web/corpus_builder/repair_dict_mojibake.py`) is bounded: 333 unrepairable
instances are flagged for a human in `web/corpus_builder/mojibake_report/`,
never rewritten.

Aux top-level surfaces: `nkrya-parallel/` (NKRYa parallel-corpus showcase,
GitHub Pages via `deploy-nkrya-parallel-pages.yml`, serving `static/llms.txt`,
H8386) and `reports/` (durable crosswalk/report artifacts, e.g. xwalk-s7
AV×DCS).

## How to run — desktop (legacy)

Open [`Index/Index_pr.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi)
in Lazarus (packages: TurboPowerIPro, LCL). Updater:
`Index/Updater/POUpdater.lpi`. Output: `Index/lib/x86_64-win64/`.
No CLI build script. Version constant `CURRENT_VERSION` in
[`Units/UpdateChecker.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/UpdateChecker.pas)
must be bumped on a desktop release; it is `1.5.1` in source and is compared
against the Update JSON `https://samskrtam.ru/software-updates/po-ors.json`.

Runtime next to `PO.EXE`: `Data/` (corpus HTML), `Programdata/` (`data.txt`
filename list, `program.ini`, `program.grp`) and `Search/` (result HTML).

## Do not touch

- Do not start a second desktop search engine or a second web indexer.
- Do not treat corpus reindex as part of the app `systemctl restart`.
- Do not commit paper/manuscript-shape files here — they live in private
  repos only (standing policy); CI `paper-priv-guard.yml` blocks them, and
  `papers/CANARY_paper_priv.md` is the positive control of the nightly
  paper-priv sweep — never delete, move or allowlist it.
- Do not rewrite `stenogrammy` / lesson-listen paths here — those belong
  to Systema / whisper keep-out rules, not this repo. Agent-tool fences for
  this repo are machine-enforced from
  [`.agent_policy.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/.agent_policy.json):
  no `.env` into git; `stenogrammy` READ-OPEN / PUBLISH-CLOSED (H8050).
- CHANGELOG: no bullet under `[Unreleased]` — one file per entry in
  `changelog_queue/`, and an entry with no `- ` line is skipped at release
  cut (H8367); the cut is Uprava `tools/cut_release.py` (H3355).
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

### Python floor sync (H7934)

The CI matrix floor is **3.10** (H7160/H1927 policy) and four places must move
together when it changes: the `python-version` matrix in
[`.github/workflows/ci.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/ci.yml),
[`dependency-floor-install.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/dependency-floor-install.yml),
the `ignore:` blocks in [`.github/dependabot.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/dependabot.yml)
(`sse-starlette >=3.6`, `python-multipart >=0.0.33`, `pydantic-settings >=2.16` —
each says "drop when 3.10 goes"), and the matching caps in `web/requirements.txt`.
A dependency pin that declares `Requires-Python >=3.11` breaks the 3.10 leg at
`pip install`, not at test time — Dependabot PRs are gated by the floor-install
check and by auto-merge's CI-green poll for exactly this reason (#447 merged red).

## Memory store

This repo keeps a committed memory store at [`.claude/projects/SamudraManthanam/memory/`](https://github.com/gasyoun/SamudraManthanam/tree/main/.claude/projects/SamudraManthanam/memory) per the org Memory-routing rule ([`/danger-memory`](https://github.com/gasyoun/claude-config/blob/main/commands/danger-memory.md)) — write dangerous/durable facts there and index each in its `MEMORY.md` (H4547).

_Dr. Mārcis Gasūns_
