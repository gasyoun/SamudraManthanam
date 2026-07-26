# ARCHITECTURE — SamudraManthanam residual lanes

_Created: 26-07-2026 · Last updated: 26-07-2026_

Companion to
[PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md).
No greenfield system — residual work plugs into existing FastAPI/SQLite/JSONL
platform.

---

## 1. System boundary (unchanged)

```
Browser (RU UI, PWA, optional offline packs)
    ↕  HTTP
FastAPI app (web/app/) — search, reader, offline, admin
    ↕
corpus.db (FTS5) + state.db (morph/corrections)
    ↑ build
canonical JSONL (web/corpus_builder/jsonl/) ← converters / ingest
```

Grey-rights: corpus ships **inside** the app/service; export APIs emit **search
result sets**, never bulk text dumps.

---

## 2. Lane A — export + hygiene

### 2.1 Search export (H1502)

**Build vs reuse:** **reuse** `dispatch_search` + existing export metadata dict
in `web/app/routers/search.py` (HTML path already works). Add serializers only.

| Format | Content-Type | Shape |
|---|---|---|
| `html` (default) | text/html | current |
| `json` | application/json | `{ meta, results: [...] }` same fields as HTML rows |
| `csv` | text/csv | header + one row per hit; stable IDs + snippet + source |

Query params: existing export params + `format=html|json|csv`. Rights: results
only (query echo, IDs, short snippets already shown in UI).

### 2.2 morph_cache (H1503)

Morph lives in **state.db** (Track B). `corpus.db.create_schema` must stop
creating dead `morph_cache`; optional one-shot DROP for existing DBs.

### 2.3 SSE stream

Keep `GET /api/search/stream`. Architecture: same search backend, event-stream
framing. **No frontend wiring** this span. Tests assert validation parity with
POST `/api/search` and a successful stream of ≥1 event on fixture data.

---

## 3. Lane B — integrity

### 3.1 Canonical ID uniqueness (DBhP)

Invariant: every emitted JSONL `id` unique per work (and globally where the
gate asserts). Known concentration: generated `devibhagavata-purana` combined
JSONL. Fix at **generator / combined-merge** layer, not by masking the gate.
Prior art: H941 combined-jsonl fix — re-verify first; extend if residual dups.

### 3.2 Cyrillic homoglyphs in `#sa` (issue #16)

Homoglyphs (Cyrillic letters that look like Latin/IAST) corrupt Sanskrit fields.
Architecture: **normalize or reject at ingest/convert and at search display
path** for `#sa` / Sanskrit script segments; keep a small golden list of the
five known words from the issue as regression fixtures. Prefer fix at write
time (JSONL) so FTS and offline packs stay clean.

---

## 4. Lane C — Ignatiev (H1438)

Pipeline already generalized: `ignatiev_book_to_canonical.py` (docx/pdf).
Remaining architecture debt **inside** H1438:

- **Māyā-tantra:** glued-digit per-page footnotes → separate front-end mode.
- **`.doc`:** `antiword` branch in `extract_text()`.
- **Commit fence:** only derived JSONL/meta/HTML; never raw archive.

No new subsystem; no Wave B–D handoff series in this plan.

---

## 5. Prior-art / do-not-rebuild

| Temptation | Already exists |
|---|---|
| New search engine | FastAPI FTS5 + offline wasm packs |
| TEI master | JSONL canonical (settled) |
| Somadeva re-align | all 18 books done |
| NKРЯ export freeze | W4 done |
| Morphology cache in corpus.db | migrated to state.db |

---

## 6. Wave-2 note (H1485)

Corpus_builder Delphi GUI vs Python engine decoupling is **orthogonal** to web
search. Defer to wave-2 so H1438 file churn in `web/corpus_builder/` does not
collide with Delphi path surgery.

_Dr. Mārcis Gasūns_
