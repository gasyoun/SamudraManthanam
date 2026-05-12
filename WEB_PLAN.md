# Web Application — Architecture & Implementation Plan

> This document is a complete technical specification for Gemini Flash (or any AI agent) to implement the browser-based version of Samudra Manthanam from scratch. Read it fully before writing any code.

---

## 1. What you are building

A web application that replicates and extends the Windows desktop search tool. Users visit `samskrtam.ru`, type a Sanskrit or Russian word, and receive a paginated HTML result page with highlighted matches grouped by source — identical in structure to the desktop output, but served over HTTP with no installation required.

The three deliverables in priority order:

1. **Core web search** — plain text, whole-word, regex, multi-query, source filtering
2. **Morphological search** — stem/root expansion across mixed IAST/SLP1/Devanagari encodings
3. **Corpus sync API** — serve corpus updates to the legacy desktop app instead of shipping data in ZIP files

---

## 2. System architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Browser                                                     │
│  index.html + search.js + style.css (same CSS as desktop)   │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS / REST+JSON / SSE
┌────────────────────────▼─────────────────────────────────────┐
│  FastAPI  (Python 3.11)                                      │
│  /api/sources   /api/search   /api/morph   /api/corpus-sync  │
│  Static: /static/** (CSS, JS, fonts, favicons)               │
└──────────────┬────────────────────────┬──────────────────────┘
               │                        │
┌──────────────▼────────┐  ┌────────────▼──────────────────────┐
│  SQLite (FTS5)        │  │  Morphological Engine             │
│  sources              │  │  indic-transliteration (PyPI)     │
│  corpus_lines (fts5)  │  │  Sanskrit Heritage morph DB       │
│  morph_cache          │  │  encoding auto-detect + expand    │
└───────────────────────┘  └───────────────────────────────────┘
               ▲
┌──────────────┴────────┐
│  Ingest Pipeline      │
│  ingest.py            │
│  Data/*.html → SQLite │
└───────────────────────┘
```

---

## 3. Repository layout to create

```
web/
  app/
    main.py              FastAPI application entry point
    routers/
      search.py          POST /api/search, GET /api/search/stream
      sources.py         GET /api/sources
      morph.py           GET /api/morph/{word}
      corpus_sync.py     GET /api/corpus-sync/manifest
    services/
      search_service.py  Core search logic (FTS5 + regex fallback)
      morph_service.py   Encoding detection, stem expansion
      html_service.py    Result → HTML rendering (port of MakeHTML_From_FindList)
    db.py                SQLite connection + schema creation
    models.py            Pydantic request/response models
  ingest/
    ingest.py            One-shot corpus → SQLite pipeline
    parse_html.py        HTML corpus file parser
  static/
    (copy from Index/lib/x86_64-win64/Search/src/ — style.css, scripts/, fonts/, favicon/)
  templates/
    index.html           Single-page search UI
    result_fragment.html Jinja2 template for AJAX result rendering
  requirements.txt
  Dockerfile
  nginx.conf
```

---

## 4. Database schema

```sql
-- Run once on startup (db.py → create_schema())

CREATE TABLE IF NOT EXISTS sources (
    id          INTEGER PRIMARY KEY,
    filename    TEXT    NOT NULL UNIQUE,
    title       TEXT    NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

-- FTS5 virtual table: tokenizes line_text for full-text search.
-- line_html is stored but NOT indexed (UNINDEXED) — used only for output.
CREATE VIRTUAL TABLE IF NOT EXISTS corpus_lines USING fts5(
    line_text,              -- HTML-stripped plain text (what is searched)
    line_html   UNINDEXED, -- Original HTML line (what is displayed)
    source_id   UNINDEXED,
    line_num    UNINDEXED,
    link_id     UNINDEXED, -- value of id= attribute on the line, if present
    chapter     UNINDEXED  -- current H1 heading at point of line
);

CREATE TABLE IF NOT EXISTS morph_cache (
    query  TEXT PRIMARY KEY,
    stems  TEXT NOT NULL    -- JSON: ["stem1","stem2",...]
);
```

---

## 5. Corpus ingestion (`ingest/ingest.py`)

Run once to populate the database. Re-run when corpus files are updated.

**Algorithm — exactly mirrors the desktop ScanFile2 logic:**

```
for each filename in Programdata/data.txt (in order):
    open Data/<filename>
    line 0: source title — strip "<!-- " prefix and " -->" suffix → sources.title
    for each subsequent line:
        extract link_id: find id="..." attribute value
        extract chapter: if line contains <H1>...</H1>, update running chapter var
        skip lines containing <head>
        strip text from <span class="endchapter"> to end of line
        plain_text = remove_html_tags(line)
        insert into corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
```

**HTML tag removal** — port `RemoveHTMLTags` from `textu.pas`:

```python
import re

VEDIC_MAP = {
    'á': 'a', 'à': 'a', 'é': 'e', 'è': 'e',
    'í': 'i', 'ì': 'i', 'ó': 'o', 'ò': 'o',
    'ú': 'u', 'ù': 'u', 'r̥': 'ṛ',
    '̀': '', '́': '',   # combining accents
}

def remove_html_tags(s: str) -> str:
    s = re.sub(r'<br>', ' ', s)
    for vedic, plain in VEDIC_MAP.items():
        s = s.replace(vedic, plain)
    s = re.sub(r'<small>.*?</small>', '', s)
    s = re.sub(r'<[^>]*>', '', s)
    s = re.sub(r'  +', ' ', s).strip()
    return s
```

---

## 6. API specification

### 6.1 `GET /api/sources`

Returns ordered list of all corpus sources.

**Response:**
```json
[
  { "id": 1, "filename": "mbh01.html", "title": "Махабхарата. Книга 1" },
  ...
]
```

### 6.2 `POST /api/search`

**Request body (JSON):**
```json
{
  "query":          "Арджун",
  "mode":           "plain",       // "plain" | "regex" | "morphological"
  "case_sensitive": false,
  "whole_word":     false,
  "source_ids":     null,          // null = all sources; or [1,3,7]
  "limit":          5000
}
```

**Response:**
```json
{
  "query":        "Арджун",
  "total":        342,
  "elapsed_ms":   180,
  "sources_hit":  12,
  "results": [
    {
      "source_id":   1,
      "source_title":"Махабхарата. Книга 1",
      "chapter":     "Адипарва",
      "line_num":    4821,
      "link_id":     "1.12.34",
      "line_html":   "<div class=\"citation_block\">...</div>"
    },
    ...
  ]
}
```

### 6.3 `GET /api/search/stream?query=...&mode=...&source_ids=...`

Server-Sent Events stream for real-time progress. Each event is a JSON line:

```
data: {"type":"progress","source_id":3,"found_so_far":47,"percent":12}
data: {"type":"progress","source_id":4,"found_so_far":89,"percent":25}
...
data: {"type":"done","total":342,"elapsed_ms":1240}
```

### 6.4 `GET /api/morph/{word}`

Returns morphological expansion of a word (all stems + inflected forms + encoding variants).

**Response:**
```json
{
  "input":    "arjuna",
  "encoding": "IAST",
  "slp1":     "arjuna",
  "variants": ["arjuna","arjunam","arjunasya","arjunena","arjunAt","arjuno"]
}
```

### 6.5 `GET /api/corpus-sync/manifest`

Used by the legacy desktop app instead of `po-ors.json`. Returns current corpus version and file list for differential sync.

```json
{
  "version":  "2026.05",
  "files": [
    { "filename": "mbh01.html", "sha256": "abc...", "size": 204800 }
  ]
}
```

---

## 7. Search service (`services/search_service.py`)

### Plain / whole-word search

Use SQLite FTS5 `MATCH` for performance on plain-text queries. Fall back to `LIKE` only for single-character queries that FTS5 cannot handle.

```python
def search_plain(db, query, case_sensitive, whole_word, source_ids, limit):
    # Build FTS5 query string
    fts_query = f'"{query}"' if whole_word else query
    
    source_filter = ""
    params = [fts_query, limit]
    if source_ids:
        placeholders = ",".join("?" * len(source_ids))
        source_filter = f"AND source_id IN ({placeholders})"
        params = [fts_query] + source_ids + [limit]
    
    sql = f"""
        SELECT source_id, line_num, link_id, chapter, line_html
        FROM corpus_lines
        WHERE corpus_lines MATCH ?
        {source_filter}
        LIMIT ?
    """
    # If case_sensitive, add: AND line_text LIKE '%' || ? || '%'
    return db.execute(sql, params).fetchall()
```

### Regex search

FTS5 does not support regex. For regex mode, scan line_text with Python `re` against rows filtered by source:

```python
def search_regex(db, pattern, case_sensitive, source_ids, limit):
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(pattern, flags)
    source_filter = f"WHERE source_id IN ({','.join('?'*len(source_ids))})" if source_ids else ""
    rows = db.execute(f"SELECT * FROM corpus_lines {source_filter}", source_ids or [])
    results = []
    for row in rows:
        if compiled.search(row["line_text"]):
            results.append(row)
            if len(results) >= limit:
                break
    return results
```

### Morphological search

1. Detect encoding of input word (see §8).
2. Convert to SLP1.
3. Look up `morph_cache` table. If miss, call `morph_service.expand(slp1_word)`.
4. Convert each returned stem/form to IAST, SLP1, and Devanagari.
5. Run `search_plain` for each variant, union results, deduplicate by `(source_id, line_num)`.

---

## 8. Morphological service (`services/morph_service.py`)

### Encoding detection

```python
from indic_transliteration import detect

DEVANAGARI_RANGE = range(0x0900, 0x0980)
IAST_MARKERS = set('āīūṛṝḷṃḥñṭḍṇśṣ')

def detect_encoding(word: str) -> str:
    if any(ord(c) in DEVANAGARI_RANGE for c in word):
        return "Devanagari"
    if any(c in IAST_MARKERS for c in word.lower()):
        return "IAST"
    return "SLP1"
```

### Conversion

Use `indic_transliteration.sanscript`:

```python
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def to_slp1(word: str, source_encoding: str) -> str:
    scheme_map = {"IAST": sanscript.IAST, "Devanagari": sanscript.DEVANAGARI, "SLP1": sanscript.SLP1}
    return transliterate(word, scheme_map[source_encoding], sanscript.SLP1)

def to_all_encodings(slp1_word: str) -> dict:
    return {
        "IAST":       transliterate(slp1_word, sanscript.SLP1, sanscript.IAST),
        "SLP1":       slp1_word,
        "Devanagari": transliterate(slp1_word, sanscript.SLP1, sanscript.DEVANAGARI),
    }
```

### Stem expansion

Option A (recommended for Phase 4): query the **Sanskrit Heritage Site API**:
```
GET https://sanskrit.inria.fr/cgi-bin/SKT/sktlex.cgi?lex=SH&q=<slp1_word>&t=xml
```
Parse returned XML for `<stem>` elements. Cache results in `morph_cache` table.

Option B (offline fallback): ship a pre-built `stems.db` SQLite file derived from the Heritage dictionary data dump.

---

## 9. HTML rendering service (`services/html_service.py`)

Port `MakeHTML_From_FindList` from `uabstractthread.pas` to Python. The output structure must be identical so the existing `style.css` and JS work unchanged.

**Output structure (same as desktop):**

```html
<html><head>
  <title>{query}</title>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="/static/style.css">
  <script>/* highlight injection — same as desktop MakeHTML */</script>
</head>
<body>
  <div class="button-container">
    <button id="prevButton">&lt;</button>
    <button id="nearestButton">=</button>
    <button id="nextButton">&gt;</button>
  </div>
  <div class="header header_1">
    При {period} пахтании... для слова „{query}"...
  </div>
  <div class="contents">
    <!-- TOC items, grouped by chapter group then by source -->
  </div>
  <div class="chapters">
    <div class="chapter">
      <!-- For each source group, then each source, then each result line -->
      <div class="chapter_title" id="chapter_N">N. Source title</div>
      <table width=1100px>...</table>
      <div class="citation_block">...original HTML line...</div>
      <hr>
    </div>
  </div>
  <script src="/static/scripts/jquery-3.6.0.min.js"></script>
  <script src="/static/scripts/clipboard.min.js"></script>
  <script src="/static/scripts/clicktoquote.js"></script>
  <script src="/static/scripts/selection.js"></script>
</body>
</html>
```

For the web version, `html_service.render_fragment(results)` returns the body content only (no `<html>`/`<head>`). The full-page render is used only for the "download as HTML" export endpoint.

---

## 10. Frontend (`templates/index.html` + `static/search.js`)

The frontend is a single HTML page with no framework dependency. Use `fetch()` for API calls and plain DOM manipulation.

### Layout

```
┌─────────────────────────────────────────────────────┐
│  Пахтанье океана          [samskrtam.ru]             │
├─────────────────────────────────────────────────────┤
│  Search: [________________________] [Найти] [+]      │
│  Mode: ● Plain  ○ Regex  ○ Morphological             │
│  ☑ Case sensitive  ☑ Whole word                     │
├─────────────────────────────────────────────────────┤
│  Sources  [All] [None]                               │
│  ☑ Махабхарата кн.1   ☑ Махабхарата кн.2  ...       │
├─────────────────────────────────────────────────────┤
│  [progress bar — shown during search]               │
├─────────────────────────────────────────────────────┤
│  Results area — injected HTML from html_service     │
└─────────────────────────────────────────────────────┘
```

### search.js behaviour

1. On form submit, open SSE connection to `/api/search/stream` for live progress bar.
2. Simultaneously POST to `/api/search` for full results.
3. When POST resolves, close SSE and inject `result_fragment.html` into results div.
4. Re-run the highlight JS inline (same logic as desktop `window.onload` script).
5. "Download HTML" button POSTs to `/api/search/export` which returns the full standalone HTML file as a download.

---

## 11. Russian inflection helpers

Port these five functions from `textu.pas` to Python (needed for the header sentence):

```python
def sklonenie_naideno_x_zapisey(x: int) -> str: ...
def sklonenie_v_y_istochnikah(y: int) -> str: ...
def sklonenie_v_n_poiskovyh_zaprosah(n: int) -> str: ...
```

The rules are already implemented in `Units/textu.pas` lines 207–257 — translate directly.

---

## 12. `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
jinja2==3.1.4
indic-transliteration==2.3.56
httpx==0.27.0          # async HTTP for Heritage API calls
aiosqlite==0.20.0      # async SQLite
pydantic==2.7.1
python-multipart==0.0.9
```

---

## 13. `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY web/ .
COPY Index/lib/x86_64-win64/Search/src/ static/
# Corpus data — mounted as a volume in production
# COPY Data/ /corpus/Data/
# COPY Programdata/ /corpus/Programdata/
ENV CORPUS_PATH=/corpus
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Production:** mount the corpus directory as a Docker volume so it can be updated without rebuilding the image.

---

## 14. `nginx.conf` (excerpt)

```nginx
server {
    listen 443 ssl;
    server_name samskrtam.ru;

    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Connection "";     # keep-alive for SSE
        proxy_buffering    off;               # required for SSE
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 15. Implementation phases

Work through these phases in order. Each phase is independently runnable and testable.

---

### Phase 1 — Corpus ingestion (implement first, no server needed)

**Files to create:** `web/ingest/parse_html.py`, `web/ingest/ingest.py`, `web/app/db.py`

**Tasks:**

1. `db.py` — implement `get_db(path)` returning an `aiosqlite` connection and `create_schema(db)` that runs the SQL from §4.
2. `parse_html.py` — implement `parse_corpus_file(path) → Iterator[dict]` where each dict is `{line_num, line_html, line_text, link_id, chapter}`. Use `re` to extract `id=` attributes and `<H1>` headings. Use `remove_html_tags()` from §5 for `line_text`.
3. `ingest.py` — CLI script: reads `CORPUS_PATH/Programdata/data.txt`, calls `parse_corpus_file` for each file, bulk-inserts into `sources` and `corpus_lines`. Print progress every 10 files. Accept `--db-path` and `--corpus-path` args.
4. Test: run `python ingest.py --corpus-path ../Index/lib/x86_64-win64`, query the DB with `sqlite3 corpus.db "SELECT count(*) FROM corpus_lines"`, verify row count is non-zero.

---

### Phase 2 — Search API (plain + regex)

**Files to create:** `web/app/main.py`, `web/app/models.py`, `web/app/routers/search.py`, `web/app/routers/sources.py`, `web/app/services/search_service.py`

**Tasks:**

1. `models.py` — define `SearchRequest` and `SearchResult` Pydantic models exactly matching §6.2.
2. `search_service.py` — implement `search_plain()` and `search_regex()` from §7. Both must return a list of dicts matching the `SearchResult.results` item schema.
3. `routers/sources.py` — `GET /api/sources` reads from `sources` table, returns JSON array.
4. `routers/search.py` — `POST /api/search` validates request, dispatches to `search_plain` or `search_regex`, returns full `SearchResult` JSON.
5. `main.py` — create `FastAPI` app, mount `/static` directory, include routers.
6. Test: `uvicorn app.main:app --reload`, then `curl -X POST /api/search -d '{"query":"Арджун","mode":"plain"}'`. Verify results match a manual `grep` on the corpus files.

---

### Phase 3 — HTML rendering service + result fragment

**Files to create:** `web/app/services/html_service.py`, `web/templates/result_fragment.html`

**Tasks:**

1. `html_service.py` — implement `render_fragment(query, results, options) → str` producing HTML matching the structure in §9. Group results by source. Build TOC. Inject highlight `<script>` block.
2. `html_service.py` — implement `render_full_page(...)` wrapping the fragment in a complete `<html>` document with correct `<head>` links to `/static/`.
3. Add `GET /api/search/export` endpoint to `routers/search.py`: accepts same params as POST search but returns `text/html` response using `render_full_page`. Set `Content-Disposition: attachment; filename="{query}.html"`.
4. Test: download the exported HTML, open in a browser, verify it looks identical to a result from the desktop app.

---

### Phase 4 — Web frontend

**Files to create:** `web/templates/index.html`, `web/static/search.js`

**Tasks:**

1. `index.html` — build the layout from §10. Source checkboxes are populated from `/api/sources` on page load. Use existing `style.css` for result area styling.
2. `search.js` — implement form submit handler:
   - Collect form values into `SearchRequest` JSON
   - Open SSE to `/api/search/stream` → update `<progress>` element
   - POST to `/api/search` → on response, inject `data.html_fragment` into `#results`
   - Re-run highlight script after injection
3. Add `data.html_fragment` field to `SearchResult` model — populated by `html_service.render_fragment()` in the search endpoint.
4. Test in browser: search for a known word, verify results render, TOC links scroll correctly, prev/next buttons navigate between highlights.

---

### Phase 5 — SSE progress stream

**Files to create:** add `routers/search.py → GET /api/search/stream`

**Tasks:**

1. Implement `search_stream()` as an `async_generator` that yields progress events per source. Run FTS5 query source-by-source in a loop instead of a single bulk query.
2. Return `EventSourceResponse` (use `sse-starlette` package, add to `requirements.txt`).
3. In `search.js`, open the SSE before the POST request; close it on the `done` event or on POST completion, whichever comes first.
4. Test: add an artificial `asyncio.sleep(0.05)` between sources in the stream generator, verify the progress bar advances smoothly.

---

### Phase 6 — Morphological search

**Files to create:** `web/app/services/morph_service.py`, `web/app/routers/morph.py`

**Tasks:**

1. `morph_service.py` — implement `detect_encoding()`, `to_slp1()`, `to_all_encodings()` from §8.
2. `morph_service.py` — implement `expand_word(slp1: str, db) → list[str]`: check `morph_cache`, if miss call Sanskrit Heritage API (§8 Option A), parse XML, store in cache, return list of SLP1 forms.
3. `morph_service.py` — implement `search_morphological(query, db, options)`: detect encoding → to SLP1 → expand → convert each form to all encodings → run `search_plain` for each → union + deduplicate by `(source_id, line_num)`.
4. `routers/morph.py` — `GET /api/morph/{word}` returns `detect_encoding`, `slp1`, and `variants` list.
5. Wire `mode="morphological"` into `routers/search.py` search dispatch.
6. Test: search for "arjuna" in IAST, verify results include lines with "arjunam", "arjunasya", etc. Search for the Devanagari form, verify same result set.

---

### Phase 7 — Corpus sync API

**Files to create:** `web/app/routers/corpus_sync.py`

**Tasks:**

1. On ingest, compute SHA-256 of each source HTML file and store in `sources.sha256` and `sources.size` columns (add to schema).
2. `GET /api/corpus-sync/manifest` returns the JSON from §6.5.
3. `GET /api/corpus-sync/file/{filename}` serves the raw HTML corpus file for the desktop app to download.
4. Update `UpdateChecker.pas` in the desktop app: add a fallback path that checks `/api/corpus-sync/manifest` and downloads only changed files (files where SHA-256 differs from the locally cached value stored in `program.ini`).

---

### Phase 8 — Deployment

**Tasks:**

1. Finalize `Dockerfile` from §13. Build image, verify `ingest.py` runs cleanly inside container against a volume-mounted corpus.
2. Write `docker-compose.yml`: one service for the web app, corpus directory mounted as a bind mount.
3. Configure `nginx.conf` per §14. Ensure `proxy_buffering off` for SSE.
4. Set up a cron job on the server: `0 3 * * * docker exec po_web python ingest/ingest.py` to re-index if corpus files are updated.
5. Update `samskrtam.ru` DNS / reverse proxy to route `/` to the new container.

---

## 16. Acceptance criteria

Before considering the implementation complete, verify all of the following manually:

- [ ] Plain search for "Арджун" returns the same count of results as the desktop app on the same corpus.
- [ ] Regex search for `Арджун.*Кришна` returns results where both names appear on the same line.
- [ ] Morphological search for "arjuna" (IAST) returns results containing at least "arjunam" and "arjunasya".
- [ ] Source filtering: deselect all but one source, verify only that source appears in results.
- [ ] Result HTML rendered in browser is visually identical to a desktop-exported result for the same query.
- [ ] "Download HTML" produces a standalone file that works offline.
- [ ] SSE progress bar moves during search and reaches 100% on completion.
- [ ] `/api/corpus-sync/manifest` returns valid JSON with correct SHA-256 values.
- [ ] Desktop app (`UpdateChecker.pas`) can fetch the manifest and download a changed corpus file.
- [ ] All API endpoints return HTTP 200 for valid requests and HTTP 422 with a meaningful message for invalid input.

---

## 17. Key constraints and pitfalls

- **Encoding**: all corpus files and all DB columns are UTF-8. Ensure `open(..., encoding='utf-8')` everywhere in Python. SQLite defaults to UTF-8 so no special handling needed there.
- **FTS5 and special characters**: Sanskrit IAST diacritics (ā, ī, ṛ …) are multi-byte UTF-8. SQLite FTS5 with the default unicode61 tokenizer handles them correctly. Do NOT use the ascii tokenizer.
- **Regex and FTS5 conflict**: when `mode="regex"`, bypass FTS5 entirely — SQLite FTS5 MATCH syntax and Python regex syntax are incompatible. Use the pure-Python scan loop from §7.
- **Result limit**: enforce `limit=5000` at the DB query level (`LIMIT ?`), not in Python, to avoid fetching millions of rows.
- **SSE and nginx buffering**: `proxy_buffering off` is required in nginx. Without it, SSE events will be held until the buffer fills, breaking the live progress bar.
- **Heritage API rate limiting**: the Sanskrit Heritage Site is a public academic service. Cache all morph lookups in `morph_cache` immediately. Do not send the same SLP1 word twice. If the API is unreachable, fall back to a plain-string search with a warning in the response.
- **Thread safety**: `aiosqlite` is async but SQLite itself is single-writer. Use WAL mode (`PRAGMA journal_mode=WAL`) to allow concurrent reads during ingest.
