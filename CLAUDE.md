# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**"Пахтанье океана"** (Churning of the Ocean / Samudra Manthanam) is a Windows desktop application for searching a parallel Sanskrit–Russian text corpus. It is built with **Lazarus / Free Pascal** (Delphi-compatibility mode) and targets x86_64-win64.

## Build

Open and build with the **Lazarus IDE**:

- Main application: `Index/Index_pr.lpi`
- Updater utility: `Index/Updater/POUpdater.lpi`

There is no command-line build script. The compiler is Free Pascal (`fpc`); the project uses `{$MODE Delphi}` throughout. Required Lazarus packages: `TurboPowerIPro`, `LCL`.

Output directory: `Index/lib/x86_64-win64/`

## Code structure

```
Units/           Shared utility units (referenced via OtherUnitFiles in .lpi)
  uTypes.pas       Shared array/record type aliases
  textu.pas        String helpers: HTML tag stripping, Russian inflection, UTF-8 ops
  _winutils.pas    File/OS helpers: file enumeration, HTTP download, grid utils
  UpdateChecker.pas  Version check + update flow (fetches JSON from samskrtam.ru)

Index/           Main application project
  Index_pr.lpr/lpi   Project entry point
  u_Index.pas      TMainForm — search UI, corpus loading, source selection
  uabstractthread.pas  TAbstractThread — threaded search worker + HTML output
  fsources.pas     TSourcesForm — source file selection dialog
  u_words.pas      TManyWordsDialog — multi-word search dialog
  uupdateform.pas  TUpdateForm — update download progress UI

Index/Updater/   Separate updater executable
  POUpdater.lpr    Waits for main process to exit, unzips update, restarts app
```

## Runtime data layout (relative to PO.EXE)

```
Data/              Corpus HTML files
Programdata/
  data.txt         Ordered list of corpus filenames (one per line, no path)
  program.ini      User settings (INI: search options, toolbar, file enable/disable)
  program.grp      Named source groups (INI: section = group name, keys = filenames)
Search/            Output HTML result files + src/ assets (CSS, JS, fonts, favicons)
```

On startup the app loads `data.txt`, prepends `Data\` to each filename, then loads the full corpus into `FilesData[]` / `FilesData_notags[]` TStringList arrays held in memory for the lifetime of the session.

## Search flow

1. User types search terms into `Memo1` (one term per line) and presses F7 or the Find button.
2. `TMainForm.FindBtnClick` spawns one `TAbstractThread` per term, up to `ProcessorCount` parallel threads.
3. Each thread calls `ScanFile2` against every enabled corpus file in the in-memory arrays.
4. Matches are collected into a `TStringList` with tab-separated fields: `FileNum<TAB>Caption<TAB>LinkID<TAB>FullHTMLLine`.
5. `MakeHTML_From_FindList` writes a standalone result HTML (with TOC, chapter navigation, highlight JS) to `Search/<sanitized_term>-<count>.html`.
6. `RunHTML` opens the file in the default browser, then simulates Ctrl+F / Ctrl+V keyboard events to paste the search term into the browser find bar.

Record limit: `iRecordLimit = 5000` (defined in `uabstractthread.pas` initialization, readable from `program.ini`).

## Update mechanism

- `UpdateChecker.pas` checks `https://samskrtam.ru/software-updates/po-ors.json` for `{"version":"x.y.z","changelog":"..."}`.
- Current version constant: `CURRENT_VERSION = '1.5.1'` in `UpdateChecker.pas` — **bump this when releasing**.
- On user confirmation, downloads `po-ors.zip` to the temp directory, then launches `POUpdater.exe` with the current PID as argument.
- `POUpdater.exe` waits for the main process to exit, unzips over the app directory, and restarts `PO.EXE`.
- On startup, the app checks for `POUpdater1.exe` (new updater shipped inside a zip) and renames it to `POUpdater.exe`, replacing the old one.

## Key conventions

- All loop indices are 1-based (`for i:=1 to List.Count`) with zero-based array access (`List[i-1]`).
- UTF-8 strings: use `lazUTF8` functions (`UTF8Length`, `UTF8Copy`, `UTF8Delete`) for multi-byte-safe operations; byte-based `Length`/`Pos`/`Copy` are used where the strings are known ASCII or where tags are being stripped.
- Source file metadata (caption/title) is stored as the **first line** of each corpus HTML file in the form `<!-- Title text -->`; `FormatFileInfo` strips the comment wrapper to extract the display name.
- The `.no_tags` sidecar files alongside each corpus HTML contain the same lines with HTML tags removed, used for case-insensitive plain-text searching (though `ScanFile2` currently searches the raw HTML line — see the duplicate assignment of `Str` at lines 548–549 of `uabstractthread.pas`).

## Web Platform

The modern web-based search engine is built with **FastAPI** and **SQLite (FTS5)**.

### Commands
- Run dev server: `cd web; python -m uvicorn app.main:app --reload`
- Run hermetic tests: `cd web; $env:PYTHONPATH="."; python -m pytest -m "not corpus"`
- Run full corpus tests: `cd web; $env:PYTHONPATH="."; $env:USE_REAL_CORPUS="1"; python -m pytest -m "corpus"`
- Build search database: `./build-web-db.ps1`
- Re-index (Docker): `./reindex.sh`

### Testing Strategy
- **API Contract**: `tests/test_api.py` (validation, security, parity).
- **Search Quality**: `tests/test_golden_queries.py` (IAST, multi-token, Russian).
- **Search Contract**: `tests/test_contract.py` (prefix matching and AND logic).
- **Morphology**: `tests/test_morph.py` (transliteration and stem lookup).

### Architecture
- `dispatch_service.py`: Unified entry point for all search modes.
- `search_service.py`: Core FTS5 logic (plain search with prefix matching).
- `morph_service.py`: Stem/Root lookup using external API.
- `html_service.py`: Secure Jinja2-based result fragment rendering.
- `settings.py`: Centralized configuration (DB_PATH).
- `models.py`: Pydantic V2 models for API requests/responses.

## Operational hazard notes

Destructive-risk facts for this repo (do-not-rerun scripts, decoys, traps) are
registered centrally in an org-private hub
([Uprava DANGER_FACTS.md](https://github.com/gasyoun/Uprava/blob/main/DANGER_FACTS.md),
org members only); the public-safe subset is mirrored in the generated block of
[AGENTS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/AGENTS.md). Check them
before running anything that writes.
