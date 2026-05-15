# Samudra Manthanam — Churning of the Ocean

A parallel Sanskrit–Russian corpus search tool developed by the [Society of Sanskrit Enthusiasts](https://samskrtam.ru). The name refers to the mythological churning of the cosmic ocean (*Samudra Manthanam*), here used as a metaphor for extracting meaning from an ocean of words.

**Current version:** 1.5.1 · **Platform:** Windows (x86-64) · **Language:** Russian UI

---

## What it does

The application lets you search a curated parallel corpus of Sanskrit texts alongside their Russian translations. For each search query it:

- scans the full corpus in parallel (one thread per query, up to CPU core count)
- produces a standalone HTML result file with a table of contents, chapter grouping, and highlighted matches
- opens the result in the default browser with the search term pre-pasted into the browser find bar

Supported search modes: plain text, whole-word, case-sensitive, and regular expressions. Multiple queries can be batched (one per line) and processed concurrently.

---

## Installation

1. Download the latest release from [samskrtam.ru](https://samskrtam.ru) or the [GitHub Releases](../../releases) page.
2. Unzip to any folder — the application is fully portable, no installer needed.
3. Run `PO.EXE`.

The application checks for updates automatically on launch and can self-update via the bundled `POUpdater.exe`.

---

## Building from source

**Requirements**

| Tool | Notes |
|---|---|
| [Lazarus IDE](https://lazarus-ide.org) | Free Pascal compiler included |
| TurboPowerIPro package | Install via Lazarus package manager |
| LCL | Bundled with Lazarus |

**Steps**

1. Clone this repository.
2. Open `Index/Index_pr.lpi` in the Lazarus IDE.
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

Index/              Main application
  u_Index.pas         Main form: search UI, corpus loading, source management
  uabstractthread.pas Threaded search worker and HTML result generator
  fsources.pas        Source file selection dialog
  u_words.pas         Multi-word search dialog
  uupdateform.pas     Update download progress dialog
  Index_pr.lpi/lpr    Lazarus project files

Index/Updater/      Self-updater utility
  POUpdater.lpr       Standalone exe: unzips update and restarts main app
```

---

## Corpus

The corpus contains Sanskrit texts with parallel Russian translations, encoded in a mix of **IAST** (diacritics), **SLP1** (ASCII transliteration), and **Devanagari** depending on the source. It is mostly complete — the major texts are present and further additions are planned.

Each corpus file is an HTML document. The first line holds the source title as an HTML comment; companion `.no_tags` files contain the same lines with tags stripped, used for plain-text indexing.

---

## Web database

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

### Search Behavior
The web platform's search behavior is governed by the **[Search Contract](web/SEARCH_CONTRACT.md)**. Key differences from the desktop version:
- **Prefix matching** is enabled by default (`arjun` matches `arjuna`).
- **AND logic** is used for multi-token searches.
- **Resource limits** (5s timeout) protect regex searches.

### Configuration
The app uses `web/app/settings.py` for configuration. The database path can be overridden via the `DB_PATH` environment variable.

---

## Roadmap

### 1. Web application

The highest priority for the next major version is migrating from a Windows desktop app to a **browser-based web application** hosted at [samskrtam.ru](https://samskrtam.ru). Goals:

- Make the corpus accessible without any local installation
- Enable full corpus search from any device and operating system
- Keep result HTML format compatible with the current desktop output

### 2. Stem/root lookup

Add stem/root-aware lookup that helps users explore related Sanskrit forms across mixed encodings (IAST, SLP1, Devanagari). The current web implementation exposes this honestly as stem/root lookup rather than promising complete inflection expansion.

### 3. Online corpus sync

Serve the corpus directly from the web backend, eliminating the need to ship large data files with every release. Users of the desktop version would be able to pull corpus updates independently of the application update cycle.

---

## Contributing

The codebase is Free Pascal / Lazarus in Delphi-compatibility mode (`{$MODE Delphi}`). A few things to keep in mind:

- All loop indices are 1-based; array access is zero-based (`List[i-1]` pattern throughout).
- Use `lazUTF8` functions (`UTF8Length`, `UTF8Copy`, `UTF8Delete`) for any multi-byte string operations; byte-level `Length`/`Pos`/`Copy` are only safe for ASCII or tag-boundary operations.
- When bumping the application version, update `CURRENT_VERSION` in `Units/UpdateChecker.pas`.
- The update server endpoint is `https://samskrtam.ru/software-updates/`. Update packages are named `po-ors.zip` and the version manifest `po-ors.json`.

---

## License

© 2013–2026 Society of Sanskrit Enthusiasts. See [samskrtam.ru](https://samskrtam.ru) for contact and licensing details.
