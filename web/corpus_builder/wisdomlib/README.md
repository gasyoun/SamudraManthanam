# wisdomlib catalog crawler

Async indexer + content downloader for [wisdomlib.org](https://www.wisdomlib.org)
as a **candidate** corpus source for Samudra Manthanam. Versioned independently
of the main platform (current tag: `wisdomlib-v0.0.1`).

> **Rights.** wisdomlib has no stated bulk-reuse licence and rests on mixed
> source material. Downloaded content (`content/`) is **gitignored and
> provisional** — do not redistribute. The index (`*.jsonl`, `CATALOG.md`) is
> bibliographic metadata only.

## Install

```sh
cd web/corpus_builder/wisdomlib
python -m pip install "httpx[http2]"     # h2 enables HTTP/2 (falls back to 1.1)
```

Python 3.11+. No other dependencies.

## Quick start

```sh
python crawl.py all                       # build the index + CATALOG.md (no download)
python crawl.py stageC --lang sanskrit --workers 1 --delay 5   # download content
python watch.py 5                         # live progress bar (separate terminal)
```

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
*by* Stage B). Examples:

```sh
python crawl.py stageC --lang sanskrit --workers 1 --delay 5   # all Sanskrit books
python crawl.py stageC --slug the-skanda-purana               # one book
python crawl.py stageC --section purana --ctype book --dry-run # preview only
```

## Politeness / rate limiting

- `--workers N` concurrent requests, `--delay S` jittered sleep held **inside**
  the worker slot → effective rate ≈ `workers/S` req/s.
- Browser-like UA + headers, HTTP/2 (graceful HTTP/1.1 fallback without `h2`),
  and `Retry-After` handling on 429/503.
- `is_block_page()` rejects soft-200 Cloudflare/challenge pages so a block is
  never cached as content nor permanently skipped by the resume check.

### Cloudflare reality (measured 2026-06-18/19)

The catalog (A/B) builds cleanly, but **Stage C is gated by a per-IP Cloudflare
block**. Confirmed findings:

- **Local/hosting IP:** a single small book downloads fine when the IP is clear
  (38/38 Skanda Purāṇa chapters verified), but volume re-triggers a **403**.
  It's driven by **cumulative request volume per IP**, not burst rate — even
  ~2 req/s eventually trips it, and an overnight ultra-gentle run yielded only
  ~8 pages in 9h before re-blocking.
- **GitHub-hosted (Azure datacenter) IPs:** **fully blocked** — 3/3 dispatched
  Actions runs downloaded 0 pages (the landing page itself 403s). So the free
  cloud-runner route does **not** work.
- This is **not** a JS/Turnstile challenge (httpx runs no JS — a browser engine
  wouldn't help) and **not** a header heuristic; it's a per-IP/ASN budget.
- **The only egress that gets through is a residential connection.** Run from a
  home network, gently (`--workers 1 --delay 5`), in small resumable sessions.

`_gentle_retry.py` (gitignored operational driver) automates the local case:
cooldown → book-by-book at `--workers 1 --delay 5` with a circuit breaker that
backs off for hours if it detects a re-block.

## Autonomous runs — GitHub Actions (self-hosted runner)

[`.github/workflows/wisdomlib-crawl.yml`](../../../.github/workflows/wisdomlib-crawl.yml)
runs one bounded, gentle, resumable Stage C pass on demand. Because GitHub's
own runners are Cloudflare-blocked (above), it is set to `runs-on: self-hosted`
and `workflow_dispatch` only (no cron). To use it:

1. **Register a runner on a residential machine** (a home PC on a normal ISP):
   repo **Settings → Actions → Runners → New self-hosted runner**, then run the
   `config.sh` / `run.sh` commands GitHub shows for that OS, e.g.
   ```sh
   ./config.sh --url https://github.com/gasyoun/SamudraManthanam --token <token>
   ./run.sh
   ```
2. **Prepare that machine:** Python 3.11 + `pip install "httpx[http2]"`.
3. **Trigger:** repo **Actions → "wisdomlib gentle crawl" → Run workflow**
   (inputs: `filters` default `--lang sanskrit`, `workers` `1`, `delay` `5`).
4. **Re-run as needed** — each pass resumes via the `content` cache; output is
   uploaded as the `wisdomlib-content` artifact and **never committed**.

The workflow checks out this repo's default branch for the crawler code.

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

## Per-word definitions (`definitions.py`)

Separate from the book crawler: fetches the `/definition/<word>` pages (allowed by
robots) and extracts which **traditions** a word appears under (Buddhism / Jainism /
Ayurveda / Vyakarana / Vedic / Vedanta / Hinduism / Sanskrit-dictionary) plus a gloss
count. It **reuses `crawl.py`'s** `fetch` / browser headers / `is_block_page`, runs
`workers=1` (HTTP/1.1 — wisdomlib drops HTTP/2 from non-residential egress) and stops
after 3 consecutive Cloudflare blocks.

> **Validated 2026-06-24** on real pages (`akshobhya`, `bodhisattva`): tradition
> extraction correct (`In Buddhism`/`In Jainism`/… → tags), gloss count = `suffix
> source` spans. End-to-end fetch succeeds over HTTP/1.1 from a residential connection.

```sh
python definitions.py selftest                 # parser unit check (no network)
python definitions.py parse cached.html        # validate the parser on a saved page
python definitions.py batch words.txt --delay 5  # one word per line, gentle
```

Output `word_traditions.jsonl` (word → traditions/glosses) is consumed by
`SanskritLexicography/RussianTranslation/src/enrich_renou_wisdomlib.py` as a tertiary,
lower-confidence Renou **V** (Buddhist/Jaina) hint. Raw HTML caches in `definitions/`
(gitignored). Same Cloudflare reality as Stage C — run gently from a residential
connection; **validate the parser with `parse` on the first real page** before bulk.

## Files

- `crawl.py` — the crawler (stages A/B/C + report)
- `definitions.py` — per-word `/definition/` fetcher → `word_traditions.jsonl`
- `watch.py` — Stage C progress watcher
- `enumerate_books.py` — original sync Stage-A enumerator (superseded by `crawl.py stageA`)
- `entries_index.jsonl`, `books_index.jsonl` — Stage A output
- `books_full.jsonl` — Stage B output
- `CATALOG.md` — generated human-readable summary
- `content/` — Stage C downloads (gitignored)

Requires `httpx[http2]` (`h2`).
