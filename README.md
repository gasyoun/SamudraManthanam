# Samudra Manthanam — Churning of the Ocean

_Created: 12-05-2026 · Last updated: 14-08-2026_

A parallel Sanskrit–Russian corpus search tool developed by the [Society of Sanskrit Enthusiasts](https://samskrtam.ru). The name refers to the mythological churning of the cosmic ocean (*Samudra Manthanam*), here used as a metaphor for extracting meaning from an ocean of words.

**Desktop app version:** 1.5.1 (`PO.EXE`, per [`Units/UpdateChecker.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/UpdateChecker.pas) and the live [`po-ors.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/samskrtam.ru_software-updates/po-ors.json) update manifest) · **Repository release:** 0.11.1 (17-07-2026; see [CHANGELOG.md](https://github.com/gasyoun/SamudraManthanam/blob/main/CHANGELOG.md)) · **Platform:** Web (FastAPI) / Legacy Windows (Lazarus) · **Language:** Russian UI

---

## What it does

Samudra Manthanam is a public Sanskrit/Russian scholarly research platform with two front ends over the same corpus:

- **Web platform (FastAPI + SQLite FTS5)** — full-text search across parallel Sanskrit texts and Russian translations, with plain-text, regex, and morphological (stem/root) expansion, a scholarly reader, and passage tools.
- **Legacy Windows desktop app (`PO.EXE`, "Пахтанье океана")** — the original Lazarus/Free Pascal search client, still maintained and self-updating from [samskrtam.ru](https://samskrtam.ru).

The platform is designed to be accessible from any device without installation, while maintaining compatibility with the existing desktop workflow.

---

## Installation (desktop app)

1. Download the latest release from [samskrtam.ru](https://samskrtam.ru) or the [GitHub Releases](https://github.com/gasyoun/SamudraManthanam/releases) page.
2. Unzip to any folder — the application is fully portable, no installer needed.
3. Run `PO.EXE`.

The application checks for updates automatically on launch and can self-update via the bundled `POUpdater.exe`.

---

## Building the desktop app from source

**Requirements**

| Tool | Notes |
|---|---|
| [Lazarus IDE](https://lazarus-ide.org) | Free Pascal compiler included |
| TurboPowerIPro package | Install via Lazarus package manager |
| LCL | Bundled with Lazarus |

**Steps**

1. Clone this repository.
2. Open [`Index/Index_pr.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi) in the Lazarus IDE.
3. Build → Compile (`Shift+F9`) or Run (`F9`).

Output lands in `Index/lib/x86_64-win64/`.

To build the updater utility separately, open `Index/Updater/POUpdater.lpi`.

**Runtime data**

The compiled binary expects the following layout next to `PO.EXE`:

```
Data/                 Corpus HTML files
Programdata/
  data.txt            Ordered list of corpus filenames
  program.ini         User settings (auto-created on first run)
  program.grp         Named source groups
Search/               Search result output + CSS/JS/font assets
```

---

## Project structure

```
Units/              Shared utility units
  uTypes.pas          Array and record type aliases
  textu.pas           String helpers: HTML stripping, Russian inflection, UTF-8
  _winutils.pas       File/OS utilities, HTTP download, grid helpers
  UpdateChecker.pas   Version check and self-update logic

Index/              Main desktop application (Lazarus / Free Pascal)
  u_Index.pas         Main form: search UI, corpus loading, source management
  uabstractthread.pas Threaded search worker and HTML result generator
  fsources.pas        Source file selection dialog
  u_words.pas         Multi-word search dialog
  uupdateform.pas     Update download progress dialog
  Index_pr.lpi/lpr    Lazarus project files

Index/Updater/      Self-updater utility
  POUpdater.lpr       Standalone exe: unzips update and restarts main app

Corpus_builder/     Legacy Delphi 7 corpus builder (cb.exe) — the authoring tool
                    that turns plain-text sources into corpus HTML files

web/                Modern FastAPI + SQLite (FTS5) web platform
  app/                Application code (search, morphology, HTML rendering)
  ingest/             Corpus → SQLite FTS ingest pipeline
  corpus_builder/     Python PDF → canonical-JSONL → app-HTML pipeline (H534)
```

See [`CLAUDE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/CLAUDE.md) for the developer-facing architecture notes and [`DOCUMENTATION_INDEX.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/DOCUMENTATION_INDEX.md) for the map of current vs. historical design docs.

---

## Corpus

The corpus contains **153 active source texts** (Sanskrit with parallel Russian translations), encoded in a mix of **IAST** (diacritics), **SLP1** (ASCII transliteration), and **Devanagari** depending on the source. The major texts are present and further additions are ongoing.

Each corpus file is an HTML document. The first line holds the source title as an HTML comment; companion `.no_tags` files contain the same lines with tags stripped, used for plain-text indexing.

New sources can be prepared with the legacy [`Corpus_builder/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder) Delphi tool (`cb.exe`) or the newer Python **PDF → canonical-JSONL → app-HTML** pipeline in [`web/corpus_builder/`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder), documented in [`PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md). The most recent addition via that pipeline is the **Devībhāgavata-purāṇa Skandha 1** (A. Ignatjev, Касталия 2018) — 20 chapters, 1181 verses, with Sanskrit aligned at 1180/1181 (99.9%) from the sanskritdocuments.org source (H534).

**Typo / errata rebuild (H2720).** Account a slip in [`web/corpus_builder/errata/<slug>/errata.yml`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/errata) (same `read` / `instead` / `found_by` / `date_added` row as [SanskritGrammar `errata.yml`](https://github.com/gasyoun/SanskritGrammar/blob/main/KnauerFrazy_1908/errata.yml); add `passage` or `id` when there is no printed page). Then, without opening `cb.exe`:

```
python web/corpus_builder/apply_errata.py --work <slug> --rebuild
```

That patches the canonical JSONL and re-runs `html-from-jsonl`. Which inbound recipe a work uses lives in [docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md) §4.5 / [`errata/recipes.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/errata/recipes.json). Pilot work: [bhagavati-manasa-puja-stotra](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/errata/bhagavati-manasa-puja-stotra/errata.yml).

---

## Web platform

The FastAPI web app uses a generated SQLite FTS database at:

```text
web/corpus.db
```

This file is about 500 MB for the current corpus and is intentionally **not tracked in Git**. GitHub blocks normal repository files above 100 MB, and this database is reproducible from the checked-in corpus data and ingest pipeline.

Build it locally from the repository root with:

```powershell
.\build-web-db.ps1
```

Equivalent direct command:

```powershell
python web\ingest\ingest.py --corpus-path Index\lib\x86_64-win64 --db-path web\corpus.db
```

For Docker Compose, create `web/corpus.db` before starting the container because `docker-compose.yml` mounts that host file into `/app/corpus.db`.

If a prebuilt database must be distributed, use a GitHub Release asset or another artifact store rather than committing the SQLite file to normal Git history.

### Running the web app

```powershell
cd web
python -m uvicorn app.main:app --reload
```

### Search behavior

The web platform's search behavior is governed by the [Search Contract](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md). Key differences from the desktop version:

- **Prefix matching** is enabled by default (`arjun` matches `arjuna`).
- **AND logic** is used for multi-token searches.
- **Resource limits** (5s timeout) protect regex searches.

### Configuration

The app uses [`web/app/settings.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/settings.py) for configuration. The database path can be overridden via the `DB_PATH` environment variable.

---

## Roadmap

The canonical planning index is
[`PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md);
live status is
[`ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md).
Near-term themes:

1. **Architecture integrity** — manifest-backed canonical JSONL, durable
   references, bounded regex, migrations, and reproducible dual deployments.
2. **Corpus growth** — complete Wisdomlib Stage C and recover/continue the
   existing Ignatiev H1438 work without duplicating pipelines.
3. **Collaborative research** — build verified/anonymous correction and
   annotation workflows only on stable corpus identity.

---

## Related site: НКРЯ / ruscorpora.ru export (`nkrya-parallel/`)

[`nkrya-parallel/`](https://github.com/gasyoun/SamudraManthanam/tree/main/nkrya-parallel) hosts a small Docusaurus site over E. A. Rubanova's 2020 HSE ВКР («Полуавтоматическая морфологическая разметка русско-санскритского параллельного корпуса») — the pilot this repo's corpus is being scaled from for a future Russian National Corpus ([ruscorpora.ru](https://ruscorpora.ru)) submission. Live at **[gasyoun.github.io/SamudraManthanam](https://gasyoun.github.io/SamudraManthanam/)**.

**Site placement caveat:** this site occupies the repo's GitHub Pages **root** (`/SamudraManthanam/`), not a `/nkrya-parallel/` subpath — a Docusaurus scaffold quirk carried over from the original deploy ([PR #38](https://github.com/gasyoun/SamudraManthanam/pull/38)). Any future SamudraManthanam Pages content (e.g. a project landing page) would collide with this root and need the thesis site moved to a subpath first. Keep root as-is unless that becomes a real need.

Rubanova's underlying working files (санскритизм stemmer lists, name indexes, deeppavlov morphology dumps) live in `nkrya-parallel/diplom-rubanova/` — only the small, reusable artifacts are tracked in git (curated lists, manual adjudications, epithet/synonym lists); the ~600 MB of raw corpus dumps and dictionary sources stay local-only, inventoried in [`diplom-rubanova/MANIFEST_LOCAL_ONLY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/MANIFEST_LOCAL_ONLY.md). Roadmap: [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md).

**Full-corpus export (Wave 4, [v0.4.0](https://github.com/gasyoun/SamudraManthanam/releases/tag/v0.4.0)).** [`web/corpus_builder/nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) `--all-ru --with-sanskritisms` now exports **every `seg=ru` source (131) — 95,260 sentence pairs** as best-guess НКРЯ para-XML + TMX 1.4b + TSV, plus a per-source sanskritisms proper-name index (byte-deterministic across runs). Committed sidecars: [`nkrya-parallel/export/RIGHTS_TABLE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md) (per-source title · translator · rights) and [`nkrya-parallel/export/FULL_CORPUS_VALIDATION.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/FULL_CORPUS_VALIDATION.md) (per-source classify() stats). The ~80 MB bulk export is in-copyright — gitignored, shipped only as the v0.4.0 release asset. **Rights gate:** only 4 of 131 sources have documented rights and all 131 are `needs_review` — verify each against the physical edition and clear it per-translator before any ruscorpora.ru submission.

---

## Contributing

The desktop codebase is Free Pascal / Lazarus in Delphi-compatibility mode (`{$MODE Delphi}`). A few things to keep in mind:

- All loop indices are 1-based; array access is zero-based (`List[i-1]` pattern throughout).
- Use `lazUTF8` functions (`UTF8Length`, `UTF8Copy`, `UTF8Delete`) for any multi-byte string operations; byte-level `Length`/`Pos`/`Copy` are only safe for ASCII or tag-boundary operations.
- When bumping the desktop application version, update `CURRENT_VERSION` in [`Units/UpdateChecker.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/UpdateChecker.pas).
- The update server endpoint is `https://samskrtam.ru/software-updates/`. Update packages are named `po-ors.zip` and the version manifest `po-ors.json`.

See [`CONTRIBUTING.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/CODE_OF_CONDUCT.md).

---

## License and corpus rights

**Code:** Apache License 2.0 (see [LICENSE](https://github.com/gasyoun/SamudraManthanam/blob/main/LICENSE)). Cite the software via [CITATION.cff](https://github.com/gasyoun/SamudraManthanam/blob/main/CITATION.cff).

**Corpus data:** the Apache license does **not** extend to the corpus texts. The Sanskrit sources are public domain, but the Russian translations (e.g. Т.Я. Елизаренкова's Ригведа, «Наука» editions) remain under the rights of their translators, editors, and publishers. The corpus is provided for non-commercial scholarly use within this application and its search service; it is not offered for redistribution. Cite passages by their print editions (each source page lists edition and translator).

© 2013–2026 Society of Sanskrit Enthusiasts. See [samskrtam.ru](https://samskrtam.ru) for contact and licensing details.

_Dr. Mārcis Gasūns_
