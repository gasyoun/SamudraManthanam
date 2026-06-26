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
--shard k/n    disjoint slice for machine k  --impersonate PROFILE  curl_cffi TLS
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
- **Path-scoped, and not TLS-fingerprint-based (measured 2026-06-26).** On a
  blocked IP the block is selective: the book **landing** page returns HTTP 200
  while its `/d/docN.html` **chapter** pages return HTTP 403 — same IP, same
  session, same instant. Swapping httpx for a real-browser TLS/JA3 fingerprint
  via `curl_cffi --impersonate` (tested `chrome`, `chrome124`, `safari`) did
  **not** change it: landing 200 / chapter 403 on all three. So `--impersonate`
  cannot rescue a blocked IP here — the gate is IP reputation on the `/d/` path,
  not the handshake. (Left in for IPs that *are* fingerprint-gated; it's free.)
- **The only egress that gets through is a residential connection.** Run from a
  home network, gently (`--workers 1 --delay 5`), in small resumable sessions.

`_gentle_retry.py` (gitignored operational driver) automates the local case:
cooldown → book-by-book at `--workers 1 --delay 5` with a circuit breaker that
backs off for hours if it detects a re-block.

### Spreading the per-IP budget across machines (`--shard`)

Because the block is a **per-IP/ASN volume budget**, the way to go faster is more
residential IPs, each carrying its own budget — not a faster parser or a browser
engine. `--shard k/n` partitions the selection into `n` disjoint slices by a
**stable md5 hash of slug**, so `n` home connections (separate houses, a friend's
network, a 4G/5G hotspot — a different ASN) each fetch a non-overlapping subset
with zero coordination:

```sh
# machine 1 (home):      python crawl.py stageC --lang sanskrit --shard 1/3 --workers 1 --delay 5
# machine 2 (hotspot):   python crawl.py stageC --lang sanskrit --shard 2/3 --workers 1 --delay 5
# machine 3 (friend):    python crawl.py stageC --lang sanskrit --shard 3/3 --workers 1 --delay 5
```

The partition is identical on every machine and every run (md5, not Python's
salted `hash()`), so a machine always owns the same books and resumes cleanly.
Merging is a plain **union** of the `content/<slug>/` directories — shards never
overlap, so there are no conflicts. For an unattended daily cadence, point each
machine's **Task Scheduler / cron** at its own `--shard k/n` line (add `--limit N`
to cap each day's work).

### TLS fingerprint (`--impersonate`)

Stackable with sharding and independent of it. `--impersonate chrome` swaps httpx
for [`curl_cffi`](https://github.com/lexiforest/curl_cffi) (`pip install curl_cffi`),
replaying a real Chrome **TLS/JA3 + HTTP-2 fingerprint**. That's distinct from the
request headers already sent (which were ruled out as the gate); Cloudflare's
per-IP bot score weighs the handshake, so a genuine-browser fingerprint can lift
the volume budget before a 403. It does **not** defeat a JS/Turnstile challenge.
Cheapest single-IP improvement to test; falls back to httpx if curl_cffi is absent.

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
   (inputs: `lang` default `sanskrit`, `workers` `1`, `delay` `5`, optional
   `shard` `k/n`).
4. **Re-run as needed** — each pass resumes via the `content` cache; output is
   uploaded as the `wisdomlib-content` artifact and **never committed**.

For **several runners on different home connections**, register one self-hosted
runner per machine and dispatch the workflow on each with a distinct `shard`
(`1/3`, `2/3`, `3/3`). The cache and artifact are keyed per shard
(`wisdomlib-content-1-3`, …), so each runner resumes and uploads only its own
disjoint slice; download all artifacts and union the `content/` dirs.

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

## Files

- `crawl.py` — the crawler (stages A/B/C + report)
- `watch.py` — Stage C progress watcher
- `enumerate_books.py` — original sync Stage-A enumerator (superseded by `crawl.py stageA`)
- `entries_index.jsonl`, `books_index.jsonl` — Stage A output
- `books_full.jsonl` — Stage B output
- `CATALOG.md` — generated human-readable summary
- `content/` — Stage C downloads (gitignored)

Requires `httpx[http2]` (`h2`).
