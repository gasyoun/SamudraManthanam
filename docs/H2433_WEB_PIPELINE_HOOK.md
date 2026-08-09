# H2433 — Corpus_builder Phase 4 web-pipeline hook

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Model:** Grok 4.5 (`grok-4.5`)

## Goal

Wire headless `cb_headless` (H2432) into a scripted step **before**
[`build-web-db.ps1`](https://github.com/gasyoun/SamudraManthanam/blob/main/build-web-db.ps1)
/ [`reindex.sh`](https://github.com/gasyoun/SamudraManthanam/blob/main/reindex.sh), so one
publish run can rebuild `Data/*.html` from source and then refresh the SQLite FTS5 DB.

## Delivered

| Piece | Path |
|---|---|
| Runner | [`scripts/run_headless_cb.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/run_headless_cb.py) |
| Jobs example | [`Corpus_builder/pipeline/headless_jobs.example.jsonl`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/pipeline/headless_jobs.example.jsonl) |
| Linux reindex hook | [`reindex.sh`](https://github.com/gasyoun/SamudraManthanam/blob/main/reindex.sh) (always calls runner before publish) |
| Windows build hook | [`build-web-db.ps1`](https://github.com/gasyoun/SamudraManthanam/blob/main/build-web-db.ps1) |
| Hermetic tests | [`web/tests/test_run_headless_cb.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_run_headless_cb.py) |
| Roadmap tick | [`Corpus_builder/ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Фаза 4 «Стык с веб-конвейером» |

## Pipeline order

```text
[optional headless jobs]
  cb_headless --build <config|work-dir> [--out HTML] [--check]
        │
        ▼
  Data/*.html  (fresh or prebuilt)
        │
        ▼
  reindex.sh → publish.py   OR   build-web-db.ps1 → ingest.py
        │
        ▼
  corpus.db (SQLite FTS5)
```

## Operator enablement

1. Build headless binary (when Lazarus present)::

   ```text
   lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi
   ```

2. Create a jobs file (JSONL). Prefer either:

   * repo: `Corpus_builder/pipeline/headless_jobs.jsonl` (gitignored if local-only), or
   * deploy: `$CORPUS_PATH/Programdata/headless_jobs.jsonl`

   Start from
   [`headless_jobs.example.jsonl`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/pipeline/headless_jobs.example.jsonl).

3. Run the normal publish path — the hook runs automatically:

   ```bash
   CORPUS_PATH=/opt/samudra/corpus DB_PATH=… /opt/samudra/repo/reindex.sh
   # Windows:
   .\build-web-db.ps1
   ```

### Environment

| Variable | Meaning |
|---|---|
| `CB_HEADLESS` | Absolute path to `cb_headless` / `cb_headless.exe` |
| `CB_HEADLESS_JOBS` | Absolute path to jobs JSONL (overrides default lookup) |
| `SKIP_HEADLESS_CB=1` | Force no-op (prebuilt HTML only) |
| `CORPUS_PATH` | Used by reindex + for `Programdata/headless_jobs.jsonl` lookup |

### Exit codes (runner)

| Code | Meaning |
|---|---|
| 0 | Success, empty/no jobs, or forced skip |
| 1 | Job failed, or jobs configured but binary missing |
| 2 | Bad/unreadable jobs file |

## Safe default for production

Prod today rsyncs prebuilt `Data/*.html` and runs reindex without source `.txt` /
`config.ini` for every book. With **no** jobs file present, the hook prints a
skip line and exits 0 — cron and
[`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) flows are
unchanged.

## Prove (hermetic)

```text
cd web
python -m pytest tests/test_run_headless_cb.py -q
```

Live binary smoke (when `lazbuild` product exists):

```text
# write one job, then:
python scripts/run_headless_cb.py --dry-run
python scripts/run_headless_cb.py
```

## Residual

* **H2434** — CI job: FPC build + golden + headless rebuild on PRs that touch source texts.
* Multi-book orchestration still in `fMainForm` (ARCHITECTURE residual) — jobs file is one row per single-book `--build`.

_Dr. Mārcis Gasūns_
