# wisdomlib catalog crawler

Async indexer + content downloader for [wisdomlib.org](https://www.wisdomlib.org)
as a **candidate** corpus source for Samudra Manthanam. Versioned independently
of the main platform (current tag: `wisdomlib-v0.0.1`).

> **Rights.** wisdomlib has no stated bulk-reuse licence and rests on mixed
> source material. Downloaded content (`content/`) is **gitignored and
> provisional** — do not redistribute. The index (`*.jsonl`, `CATALOG.md`) is
> bibliographic metadata only.

## Pipeline

| Stage | Command | Output |
|---|---|---|
| A — enumerate | `python crawl.py stageA` | `entries_index.jsonl` (848 non-Marathi entries from 46 topic sections) |
| B — enrich | `python crawl.py stageB [--workers N]` | `books_full.jsonl` (source language, English-translation flag, chapter count) — resumable |
| report | `python crawl.py report` | `CATALOG.md` (totals, breakdowns, top-25, fetch failures) |
| C — content | `python crawl.py stageC [filters]` | `content/<slug>/doc*.html` raw chapters — resumable per page **and** per book |
| (all) | `python crawl.py all` | A + B + report (**not** C) |

robots.txt is respected: only section pages, `/book|essay|...` landings, and
`/d/docN.html` content are fetched; the Disallow'd `/books?l=`,
`print-chapter.php`, search, journals and `?i=`/`?l=` params are never requested.

## Selection filters (Stage B universe and Stage C)

AND-combined; repeatable or comma-lists where noted.

```
--section S    topic section(s)            --slug S      explicit slug(s)
--ctype T      book|essay|article|...       --english     has an English translation
--lang L       source_lang (Stage C only)  --pali/--no-pali
--min-words N  size floor                   --limit N     cap the selection
```

`--lang`/`--english`/`--pali` only select on Stage C (those fields are produced
*by* Stage B). Example — Sanskrit-source books, polite rate:

```sh
python crawl.py stageC --lang sanskrit --workers 1 --delay 5
python watch.py 5     # live progress bar in another terminal
```

## Politeness / rate limiting

- `--workers N` concurrent requests, `--delay S` jittered sleep held **inside**
  the worker slot → effective rate ≈ `workers/S` req/s.
- Browser-like UA + headers, HTTP/2 (graceful HTTP/1.1 fallback without `h2`),
  and `Retry-After` handling on 429/503.
- `is_block_page()` rejects soft-200 Cloudflare/challenge pages so a block is
  never cached as content nor permanently skipped by the resume check.

### Cloudflare reality (2026-06-18)

The catalog (A/B) built cleanly, but **Stage C is rate-limited at the IP level**.
Findings:

- A single small book downloads fine when the IP is clear (38/38 Skanda Purāṇa
  chapters verified). But a broader run re-triggers a Cloudflare **403** block —
  it's driven by **cumulative request volume per IP**, not burst rate, so even
  2 req/s eventually trips it on a sensitised IP.
- This is **not** a JS/Turnstile challenge (httpx runs no JS — a browser engine
  wouldn't help) and **not** a header heuristic; it's a per-IP budget.
- Mitigation: long cooldowns + very gentle pacing (`--workers 1 --delay 5`,
  small slices), or a **different egress IP**. Everything is resumable, so bulk
  download is best done as many small sessions over time.

`_gentle_retry.py` (gitignored operational driver) automates this: cooldown →
book-by-book at `--workers 1 --delay 5` with a circuit breaker that backs off
for hours if it detects a re-block.

## Watcher

`watch.py` mirrors the NWS scraper's watcher. Stage C writes
`content/_manifest.json` (selected books + chapter counts + the invoking argv);
`watch.py` reads it for the denominator and can `--supervise` (relaunch the same
selection on a stall).

```
python watch.py            # bar every 5%
python watch.py 10         # every 10%
python watch.py --once     # print current status once
python watch.py --supervise
```

## Files

- `crawl.py` — the crawler (stages A/B/C + report)
- `watch.py` — Stage C progress watcher
- `enumerate_books.py` — original sync Stage-A enumerator (superseded by `crawl.py stageA`)
- `entries_index.jsonl`, `books_index.jsonl` — Stage A output
- `books_full.jsonl` — Stage B output
- `CATALOG.md` — generated human-readable summary
- `content/` — Stage C downloads (gitignored)

Requires `httpx[http2]` (`h2`).
