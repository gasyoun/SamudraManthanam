_Created: 25-08-2026 · Last updated: 05-09-2026_

# Decisions needed — human input required

Open decisions that the autonomous work has surfaced but should not make
unilaterally (product, perf, or rights judgment calls). Each entry states the
finding, the options, and a recommendation. Resolve by editing this file or
telling me which option to take.

---

## D1. Base offline-search pack is 206 MB — exceeds the 130 MB gate  ✅ RESOLVED (gzip-on-wire, 2026-06-13)

**Resolution (option 1 chosen):** packs are now served **gzip-on-wire**. The build
writes a deterministic `{type}.db.gz` next to the `.db`; the endpoint serves it
with `Content-Encoding: gzip`; the browser decodes transparently so the
client-side SHA-256 still matches the raw-`.db` sidecar. The size gate now
measures the **wire** (`.gz`) size:

| Pack | Rows | Raw (OPFS) | **Wire (gated)** | Gate | Status |
|---|---|---|---|---|---|
| base | 320,902 | 206 MB | **79 MB** | 130 MB | ✅ ships |
| dict | 254,037 | 88 MB | **38 MB** | 90 MB | ✅ ships |

Browser-verified end-to-end (38/79 MB wire, decoded SHA matches, durable
install, progress 0→100 via `pack_bytes`). nginx hardened against double-gzip
(`deploy/samudra.nginx`). **Remaining caveat:** gzip fixes the *download*, not the
*on-disk OPFS footprint* — base is still 206 MB in the user's storage. If that
becomes a problem on low-end devices, do option 2 below (base-core + commentary
split). Not urgent (quota observed ≈2.5 GB).

<details><summary>Original analysis (for reference)</summary>

**Found:** Phase 3d, 2026-06-13. Building the real packs from corpus `v2026.06.13`:

| Pack | Sources | Rows | On-disk | gzip (wire) | Gate | Status |
|---|---|---|---|---|---|---|
| base | 146 | 320,902 | **206 MB** | 79 MB (39%) | 130 MB | **FAILS gate** |
| dict (MW+Apte) | 2 | 254,037 | 88 MB | 38 MB (44%) | 90 MB | OK, ships |

The design estimate (base ≤120 MB, `docs/OFFLINE_SEARCH_DESIGN.md` §3.3) was
~70% low. 206 MB on-disk OPFS + a heavy download is a poor mobile experience,
and CI's size gate (`build_offline_pack.py`, exit 1) blocks it.

**The dict pack is fully working and verified** (install → persist across reload
→ FTS5 query incl. IAST → version-sync → remove, in desktop Chrome). Only the
base pack is blocked.

**Options:**
1. **Serve packs gzipped** (`Content-Encoding: gzip`). Cuts the *download* to
   79 MB (base) / 38 MB (dict); the browser decodes transparently and the
   client-side SHA-256 still matches the raw `.db`. Does **not** reduce on-disk
   OPFS usage (still 206 MB). Needs the install progress bar to handle the
   Content-Length-is-compressed / received-is-decoded mismatch (already clamped
   to ≤100% in `search-offline.js`, but the bar will appear to stall near the
   end). Raise the size gate to measure the gzipped artifact instead of on-disk.
2. **Split base into `base-core` + `commentary` add-on**, like the dict add-on.
   Core (translations + Sanskrit, ~166k rows) would land well under 130 MB;
   commentary (~154k rows) becomes a second optional download. More build/UI
   surface, best UX (most users want core, not full commentary offline).
3. **Ship base without the prebuilt FTS5 index; rebuild it client-side on
   install.** Smaller download, but install does heavy CPU work on-device and
   on a phone that can be slow/janky.
4. **Raise the base gate to ~210 MB** and accept the size. Simplest; worst UX.

**Recommendation:** (1) now (quick, ships base immediately at 79 MB on the wire),
then (2) as the real fix when there's time. (1)+(2) compose.

</details>

---

## D2. Main-page offline search  ✅ RESOLVED (implemented, 2026-06-13)

**Resolution:** implemented + browser-verified. Confirmed empirically that the
worker loads and `opfs-sahpool` works on `index.html` (which is NOT cross-origin
isolated) — a pack installed on `/offline-settings` is queryable from the main
page. Wired:
- `web/static/scripts/offline-search-bridge.js` — ES module, sets
  `window.SamudraOffline`; **lazy** (spins up the worker only on the `offline`
  event / first offline search, so online users pay nothing); searches across
  installed packs; renders a clearly-marked degraded plain-text result list with
  highlighting + reader links (titles resolved via `listSources`).
- `web/static/search.js` — offline routing gated strictly on
  `navigator.onLine === false` (online path byte-identical); a network-status
  pill (● Онлайн / ○ Офлайн · локальный поиск / нет индекса); morphological
  search shows a network-only message offline.
- `web/templates/index.html` — loads the bridge + the pill.

Verified: offline `dharma` → 1486 hits with correct dict titles (Monier-Williams,
Apte) + reader links; online search unaffected (hits `/api/search`, rich
fragment); pill flips with online/offline events. 6 hermetic guard tests
(`test_phase3e.py`).

**Bonus — D-below confirmed:** because the worker now demonstrably loads on a
non-isolated page, COEP on `/offline-settings` is confirmed removable (the
related simplification noted below). Left for a follow-up since it needs the
`test_phase3c` COEP assertions updated.

<details><summary>Original analysis (for reference)</summary>

**Found:** Phase 3d, 2026-06-13. The durable VFS we ended up using
(`opfs-sahpool`) needs **no cross-origin isolation** — so offline search can run
on `index.html` *without* enabling global COEP (which would have broken the
Google Fonts on that page). The original design (§7.1) assumed this needed a
COEP/font decision; it does not.

What's left to wire (a future phase, not done): an "Онлайн/Офлайн" pill on the
main search page, routing the existing jQuery search to `searchOffline()` when
`navigator.onLine === false` and a pack is installed, and a minimal client-side
renderer for offline result rows (the pack stores plain `line_text`, no HTML, so
offline results are plain-text + a link to the cached reader page — intentionally
a degraded, clearly-marked fallback).

**Decision:** Do you want main-page offline search next, or keep offline search
confined to `/offline-settings` for now? It's purely additive and low-risk given
the storage path is proven, but it touches the most-used surface (`search.js`).

**Recommendation:** Yes, as its own phase (3e), after D1 so there's a base pack
worth searching.

**Related simplification (untested, do not do blindly):** because opfs-sahpool
needs no isolation, `/offline-settings` may not need COEP *at all*. The worker
only requires COEP-on-its-script *because the page is isolated*; drop COEP from
the page and the worker-script COEP requirement disappears too, while sahpool
keeps working. If verified, this removes the entire CORP+COEP middleware branch
and the page-level COEP. Worth a 10-minute browser test before committing —
left in place for now because it's load-bearing as currently wired and
`test_phase3c` asserts COEP presence.

</details>

---

## D3. `sqlite3-worker1.mjs` vendored but unused  ✅ RESOLVED (deleted, 2026-06-13)

**Deleted** `web/static/wasm/sqlite3-worker1.mjs` (559 KB). Verified safe: no
reference in any of our scripts or tests; the only mention is inside `sqlite3.mjs`'s
`sqlite3Worker1Promiser` factory (`new Worker(new URL("sqlite3-worker1.mjs", …))`),
which only runs if the promiser is *called* — our worker uses `mod.default()`
(`sqlite3InitModule`) + `installOpfsSAHPoolVfs`, never the promiser. Browser
re-verified after deletion: worker still loads (`opfs-sahpool`), full install +
IAST query work, and the file 404s. Remaining vendored wasm assets
(`sqlite3.wasm`, `sqlite3.mjs`, `sqlite3-opfs-async-proxy.js`) are all still in use.

---

## D5. GRETIL-TEI ingestion — which titles get a Russian-source search budget?

**Found:** H308, 2026-07-07. Corpus-lexicon alignment (Track A,
`Uprava/GTD_NEXT_ACTIONS.md`) needs verse-aligned Sanskrit+Russian JSONL for
~12 target titles; none exist yet. `web/corpus_builder/gretil_tei_to_canonical.py`
(new, this session) now converts a GRETIL-TEI source's **Sanskrit side** into
canonical JSONL — verified on the pilot title, Hitopadeśa (1,467 records: 709
verse + 757 prose, round-trip ID stable, one genuine source gap flagged
`needs_review` rather than guessed). `web/corpus_builder/jsonl/hitopadesha.jsonl`
is committed as the Sanskrit-only half; no Russian side exists yet, so it is
**not** run through `RussianTranslation/src/add_corpus_text.py` — that step
needs a real Russian translation, not an untranslated placeholder (the
`13_mahabharata-anushasanaparva` trap this org already excludes).

**What's genuinely blocked on a human call, per title** (not agent-resolvable —
searching/rights-clearing a translation is a scoping judgment, not a lookup):

| Title | Sanskrit side | Russian side | Open question |
|---|---|---|---|
| Hitopadeśa | ✅ converted (`hitopadesha.jsonl`) | not found | Several old RU translations exist in the literature (verse-numbered fable, should anchor cleanly on `{ch}.{v}` once found) — digitization status unknown. Best pilot candidate once a source is found. |
| Kādambarī | 2 TEI files present (Bāṇa's prose + Abhinanda's verse summary) — **not yet converted**, div-based prose structure needs its own anchoring decision (see below) | only a glossary found (`slovar-grintsera-iz-bada-kadambari.jsonl`) — wrong genre | Does a running RU prose translation of Kādambarī exist at all? If not, is this title simply not alignable, or is machine/assisted translation in scope? |
| Viṣṇu Purāṇa | **no GRETIL TEI found locally at all** | prose JSONL exists (`vishnu-purana.jsonl`, no `id=` anchors) | Sanskrit source needs sourcing before anything else; separately, Erman/Vasilkov print editions may or may not be digitally available. |
| Rāmāyaṇa Yuddha-/Uttarakāṇḍa (books 6-7) | ✅ converted H765 (`06_ramayana-yuddhakanda.jsonl` 4,436 verse records, `07_ramayana-uttarakanda.jsonl` 2,690 verse records; source `GRETIL-1_sanskr/tei/sa_rAmAyaNa.xml`, new `gretil_ramayana_kanda_to_canonical.py` — this TEI uses an `xml:id`-on-`<lg>` convention, not the H308 Track-1 inline-marker one) | the 4 already-ingested kāṇḍas (Bāla/Ayodhyā/Araṇya/Sundara) pair with П. А. Гринцер's translation (Ладомир/Наука 2006) — unconfirmed whether that edition covers books 6-7 at all | Does a Гринцер (or other) RU translation of Yuddha-/Uttarakāṇḍa exist and is it digitized? valmiki.iitk.ac.in (a candidate RU/EN source) is currently unreachable — TLS cert served for it names an unrelated domain (`ai.sugyapt.co.in`), looks like a dead/repurposed domain, not a transient outage. Kiṣkindhākāṇḍa (book 4) remains the one still-missing kāṇḍa (flagged H308, unresolved). |

**For prose titles with no verse numbers** (Kādambarī, Vishnu Purāṇa prose
portions), this converter's chapter-scoped `c{N}.p{n}` paragraph anchor
(borrowed from `CONVERTER_SPEC.md`'s Path C-prose) is a reasonable default,
but is not proven against TEI `<div>` structures — those files have no inline
verse markers like Hitopadeśa's `// Hit_ch.v //`, so before converting them the
anchoring unit (paragraph vs. printed page vs. TEI `<div>` id) needs a
per-genre call.

**Recommendation:** a human should decide which of the ~12 titles get a
Russian-source search budget (and whether OCR + rights clearance of a
print-only translation is in scope for any of them), starting with Hitopadeśa
since its Sanskrit side is already staged and it has the best odds of an
existing digitized RU translation.

---

## D4. App JS goes stale after deploy  ✅ RESOLVED (2026-06-13)

**Resolution** — the staleness had THREE layers, all now fixed, plus a
pre-existing PWA bug found along the way:

1. **HTTP caching.** App JS/CSS is served `Cache-Control: no-cache` (revalidates
   → cheap 304 when unchanged, fresh on change); vendored sqlite-wasm
   (`/static/wasm/`) + fonts get 1-year `immutable`. Set in BOTH the FastAPI
   `security_headers` middleware (dev / Docker) and `deploy/samudra.nginx`
   (prod, which bypasses the app — split into a regex location for vendored
   binaries + the prefix location for app code). Verified: 304 on conditional
   GET; correct policy per asset type.
2. **Service worker.** `sw.js` cache-first'd ALL `/static/` — which serves stale
   app code forever regardless of HTTP headers (the SW sits in front of the HTTP
   cache). App JS/CSS now uses **stale-while-revalidate** (serve cache fast,
   refresh in background → next load fresh); only `/static/{wasm,fonts,icons}/`
   stay cache-first. `SW_VERSION` bumped 1→2 to flush the v1 cache.
3. **`/sw.js` itself** is served `no-cache` so an updated SW is picked up
   promptly.

**Pre-existing PWA bug found + fixed:** `PRECACHE_URLS` listed `/sources`, which
404s (only `/api/sources` exists), and `cache.addAll` is all-or-nothing — so the
SW install **always failed and the PWA never worked offline at all**. Removed the
bad URL and made install resilient (`Promise.allSettled` + per-URL `cache.add`).
Browser-verified: SW now installs, activates, precaches 12 URLs, controls the
page; the sqlite-wasm worker still loads through it and offline search works.

The `?v=` cache-busts are kept frozen as belt-and-suspenders but are no longer
load-bearing (no manual bumping needed). 4 hermetic guards added.

<details><summary>Original analysis (for reference)</summary>

**Found:** Phase 3d, 2026-06-13, while reviewing `deploy/samudra.nginx`. The
`location /static/` block sets `Cache-Control: public, max-age=604800, immutable`.
That's correct for content-hashed/vendored assets (the wasm, woff2) but WRONG for
the app's own JS (`search.js`, `offline.js`, `search-offline.js`,
`search.worker.js`), whose URLs are not content-hashed: after a deploy, browsers
keep the old JS for up to 7 days and never revalidate.

**Partial mitigation already in place:** `search-offline.js` loads the worker as
`search.worker.js?v=WORKER_VERSION` (bump the constant when editing the worker) —
this busts the one file most likely to break silently. But `search-offline.js`
and `offline.js` themselves are still cached immutable.

**Options:** (a) drop `immutable` (or shorten `max-age`) for `*.js` under
`/static/scripts/` while keeping long immutable caching for `*.wasm`/`*.woff2`
via a more specific nginx `location ~ \.(wasm|woff2)$`; (b) add a content-hash or
`?v=` to every module URL. **Recommendation:** (a) — one extra nginx location,
no app changes. Pre-existing (affects all app JS, not just offline), so out of
scope for the gzip work, but it will bite any future JS fix.

</details>

---

## D6. Corpus_builder Phase 5 — keep LCL GUI or CLI + light web?  ⏸ DEFERRED (not enough data, 14-08-2026)

**Found:** H2435, 14-08-2026, Grok 4.6 (`grok-4.6`). After Phases 0–4, [ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 5 asks a human to pick A (keep the LCL desktop GUI for translators) or B (drop it for CLI + a light web). Soft dependency H2432 shipped ([PR #201](https://github.com/gasyoun/SamudraManthanam/pull/201)), so B is a real option.

**Human 14-08-2026:** «not enough data to rule». A vs B not picked. GUI stays.

**Clone census (same day):** one `01/02/03` triple (golden fixture only); zero ManyBooks inputs; no local Lazarus `cb.exe` / `cb_headless.exe`; committed Delphi `cb.exe` mtime 2026-05-14; 269 jsonl / 193 html.

**Still needed before A/B:** (1) a private `01/02/03` or `ManyBooks_*` workspace that someone still opens in desktop `cb`? (2) will any of the 193 `Data/*.html` titles be rebuilt via `cb`?

**Brief:** [Corpus_builder/docs/DECIDE_BRIEF_p5-gui-lcl-vs-cli_14-08-2026.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/docs/DECIDE_BRIEF_p5-gui-lcl-vs-cli_14-08-2026.md). Default until those facts exist: C (keep files, spend nothing).

_Dr. Mārcis Gasūns_
